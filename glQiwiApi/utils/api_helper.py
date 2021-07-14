import asyncio
import base64
import concurrent.futures as futures
import datetime
import functools as ft
import hashlib
import hmac
import pathlib
import re
import time
from contextvars import ContextVar
from copy import deepcopy
from http import HTTPStatus

import aiofiles
import pytz
from pydantic import ValidationError, BaseModel
from pytz.reference import LocalTimezone

from glQiwiApi.types import OperationType
from glQiwiApi.utils import errors

try:
    import orjson  # type: ignore
except (ModuleNotFoundError, ImportError):  # pragma: no cover # type: ignore
    import json as orjson  # type: ignore

# Gets your local time zone
Local = LocalTimezone()


def check_result(error_messages, content_type, status_code, request_info, body):
    """
    Checks whether `result` is a valid API response.
    A result is considered invalid if:
        - The server returned an HTTP response code other than 200
        - The content of the result is invalid JSON.

    :param error_messages:
    :param status_code: status code
    :param content_type: content type of result
    :param body: body of response
    :param request_info: info about request
    :return: The result parsed to a JSON dictionary
    :raises ApiException: if one of the above listed cases is applicable
    """

    if content_type != "application/json":
        raise errors.NetworkError(
            f'Invalid response with content type {content_type}: "{body}"'
        )

    try:
        result_json = orjson.loads(body)
    except ValueError:
        result_json = {}

    if status_code == HTTPStatus.OK:
        return result_json

    raise errors.RequestError(
        message=error_messages[status_code],
        status_code=status_code,
        traceback_info=request_info,
    )


def measure_time(func):
    """
    Декоратор для замера времени выполнения функции

    :param func:
    """

    @ft.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.monotonic()
        result = await func(*args, **kwargs)
        execute_time = time.monotonic() - start_time
        print(f"Function `{func.__name__}` executed for {execute_time} secs")
        return result

    return wrapper


def datetime_to_str_in_iso(obj, *, yoo_money_format=False):
    """
    Converts a date to a standard format for API's

    :param obj: datetime object to parse to string
    :param yoo_money_format: boolean
    :return: string - parsed date
    """
    if not isinstance(obj, datetime.datetime):
        return ""
    if yoo_money_format:
        # Приводим время к UTC,
        # так как yoomoney апи принимает именно в таком формате
        # fmt: off
        return pytz.utc.localize(obj).replace(tzinfo=None).isoformat(" ").replace(" ", "T") + "Z"
        # fmt: on
    local_date = str(datetime.datetime.now(tz=Local))
    pattern = re.compile(r"[+]\d{2}[:]\d{2}")
    from_pattern = re.findall(pattern, local_date)[0]
    return obj.isoformat(" ").replace(" ", "T") + from_pattern


def parse_auth_link(response_data):
    """
    Parse link for getting code, which needs to be entered in the method
    get_access_token

    :param response_data:
    """
    regexp = re.compile(r"https://yoomoney.ru/oauth2/authorize[?]requestid[=]\w+")
    return re.findall(regexp, str(response_data))[0]


def check_dates(start_date, end_date, payload_data):
    """ Check correctness of transferred dates and add it to request """
    if isinstance(start_date, (datetime.datetime, datetime.timedelta)) and isinstance(
        end_date, (datetime.datetime, datetime.timedelta)
    ):
        if (end_date - start_date).total_seconds() > 0:
            payload_data.update(
                {
                    "startDate": datetime_to_str_in_iso(start_date),
                    "endDate": datetime_to_str_in_iso(end_date),
                }
            )
        else:
            raise ValueError("end_date не может быть больше чем start_date")
    return payload_data


def parse_commission_request_payload(default_data, auth_maker, pay_sum, to_account):
    """Set commission payload"""
    payload = deepcopy(default_data)
    payload.headers = auth_maker(payload.headers)
    payload.json["purchaseTotals"]["total"]["amount"] = pay_sum
    payload.json["account"] = to_account
    return payload, "99" if len(to_account) <= 15 else None


def parse_card_data(
    default_data,
    trans_sum,
    to_card,
    auth_maker,
):
    """Set card data payload"""
    data = deepcopy(default_data)
    data.json["sum"]["amount"] = trans_sum
    data.json["fields"]["account"] = to_card
    data.headers = auth_maker(headers=data.headers)
    return data


def parse_headers(content_json=False, auth=False):
    """
    Функция для добавления некоторых заголовков в запрос
    """
    headers = {
        "Host": "yoomoney.ru",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    if content_json:
        headers.update({"Accept": "application/json"})
    if auth:
        headers.update({"Authorization": "Bearer {token}"})
    return headers


def set_data_to_wallet(data, to_number, trans_sum, comment, currency):
    """
    Setting data for "wallet to wallet" transfer

    :param data:
    :param trans_sum:
    :param to_number:
    :param comment:
    :param currency:
    """
    data.json["sum"]["amount"] = str(trans_sum)
    data.json["sum"]["currency"] = currency
    data.json["fields"]["account"] = to_number
    data.json["comment"] = comment
    data.headers.update({"User-Agent": "Android v3.2.0 MKT"})
    return data


def set_data_p2p_create(
    wrapped_data, amount, life_time, comment, theme_code, pay_source_filter
):
    """
    Setting data for p2p form creation transfer

    :param wrapped_data:
    :param amount:
    :param life_time:
    :param comment:
    :param theme_code:
    :param pay_source_filter:
    """
    wrapped_data.json["amount"]["value"] = str(amount)
    wrapped_data.json["comment"] = comment
    wrapped_data.json["expirationDateTime"] = life_time
    if isinstance(pay_source_filter, list):
        source_filters = " ".join(pay_source_filter).replace(" ", ",")
        wrapped_data.json["customFields"]["paySourcesFilter"] = source_filters
    if isinstance(theme_code, str):
        wrapped_data.json["customFields"]["themeCode"] = theme_code
    if not isinstance(theme_code, str) and pay_source_filter not in [
        "qw",
        "card",
        "mobile",
    ]:
        wrapped_data.json.pop("customFields")
    return wrapped_data.json


#
def multiply_objects_parse(lst_of_objects, model):
    """
    Function to handle list of objects

    :param lst_of_objects: usually its response.response_data
    :param model: pydantic model, which will parse data
    """
    objects = []
    for obj in lst_of_objects:
        try:
            if isinstance(obj, dict):
                obj: str
                objects.append(model.parse_obj(obj))
                continue
            for detached_obj in obj:
                objects.append(model.parse_obj(detached_obj))
        except ValidationError as ex:
            print(ex.json(indent=4))
    return objects


def simple_multiply_parse(objects, model):
    """
    Parse simple objects, which cant raise ValidationError

    :param objects: usually its response.response_data
    :param model: pydantic model, which will parse data
    """
    result = []
    for obj in objects:
        result.append(model.parse_obj(obj))
    return result


def take_event_loop(set_debug: bool = False):
    """
    Get new or running event loop
    !THIS FUNCTION IS IRRELEVANT, DON'T USE IT!

    :param set_debug:
    """
    try:
        loop = asyncio.get_running_loop()
        if loop.is_closed():
            raise RuntimeError()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.set_debug(set_debug)
    return loop


def hmac_key(key, amount, status, bill_id, site_id):
    """
    Функция расшифровки подписи webhook

    :param key: ключ webhook, закодированный в Base64
    :param amount: сумма p2p платежа
    :param status: статус платежа
    :param bill_id: unique p2p id
    :param site_id:
    """
    invoice_params = bytes(
        f"{amount.currency}|{amount.value}|{bill_id}|{site_id}|{status.value}", "utf-8"
    )
    return hmac.new(bytes(key), invoice_params, hashlib.sha256).hexdigest()


def hmac_for_transaction(
    webhook_key_base64, amount, txn_type, account, txn_id, txn_hash
):
    invoice_params = f"{amount.currency}|{amount.amount}|{txn_type}|{account}|{txn_id}"
    webhook_key = base64.b64decode(bytes(webhook_key_base64, "utf-8"))
    # fmt: off
    return hmac.new(webhook_key, invoice_params.encode("utf-8"), hashlib.sha256).hexdigest() == txn_hash
    # fmt: on


def custom_load(data):
    """
    Custom loads for each pydantic model, because
    it guard API from different errors

    :param data: class data
    """
    return orjson.loads(orjson.dumps(data))


class Parser(BaseModel):
    """ Модель pydantic для перевода строки в datetime """

    dt: datetime.datetime


class allow_response_code:  # NOQA
    def __init__(self, status_code) -> None:
        self.status_code = status_code

    def __call__(self, func):
        status_code = self.status_code

        @ft.wraps(func)
        async def wrapper(*args, **kwargs):
            from glQiwiApi import RequestError

            try:
                await func(*args, **kwargs)
            except RequestError as error:
                if error.status_code == str(status_code):
                    info = error.traceback_info
                    return {"success": True} if not info else info
                return {"success": False}

        return wrapper


def qiwi_master_data(ph_number, data):
    payload = deepcopy(data)
    payload["fields"]["account"] = ph_number
    return payload


def to_datetime(string_representation):
    """
    Вспомогательная функция для перевода строки во время

    :param string_representation: дата в виде строки
    :return: datetime representation
    """
    try:
        dictionary = {"dt": string_representation}
        return Parser.parse_obj(dictionary).dt
    except (ValidationError, orjson.JSONDecodeError) as ex:
        return ex.json(indent=4)


def new_card_data(ph_number, order_id, data):
    payload = deepcopy(data)
    payload["fields"].pop("vas_alias")
    payload["fields"].update(order_id=order_id)
    payload["fields"]["account"] = ph_number
    return payload


def sync_measure_time(func):
    """
    Decorator, which measures time your synchronous functions

    :param func:
    """

    @ft.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.monotonic()
        result = func(*args, **kwargs)
        execute_time = time.monotonic() - start_time
        print(f"Function `{func.__name__}` executed for {execute_time} secs")
        return result

    return wrapper


def parse_amount(txn_type, txn):
    amount = txn.amount if txn_type == "in" else txn.amount_due
    comment = txn.comment if txn_type == "in" else txn.message
    return amount, comment


def check_params(amount_, amount, txn, transaction_type):
    if amount is not None:
        if amount_ >= amount:
            if txn.direction == transaction_type:
                return True
    return False


def run_forever_safe(loop) -> None:
    """ run a loop for ever and clean up after being stopped """

    loop.run_forever()
    # NOTE: loop.run_forever returns after calling loop.stop

    safe_cancel(loop=loop)


def safe_cancel(loop) -> None:
    """cancel all tasks and close the loop gracefully"""

    loop_tasks_all = asyncio.all_tasks(loop=loop)

    for task in loop_tasks_all:
        task.cancel()
    # NOTE: `cancel` does not guarantee that the task will be cancelled

    for task in loop_tasks_all:
        if not (task.done() or task.cancelled()):
            try:
                # wait for task cancellations
                loop.run_until_complete(task)
            except asyncio.CancelledError:
                pass
    # Finally, close event loop
    loop.close()


def _await_sync(future):
    """ synchronously waits for a task """
    return future.result()


def _cancel_future(loop, future, executor) -> None:
    """ cancels future if any exception occurred """
    executor.submit(loop.call_soon_threadsafe, future.cancel)


def _stop_loop(loop) -> None:
    """ stops an event loop """
    loop.stop()


class AdaptiveExecutor(futures.ThreadPoolExecutor):
    """ object: AdaptiveExecutor """

    def __init__(self, max_workers=None, **kwargs):
        super().__init__(max_workers, "sync_adapter_", **kwargs)
        self.max_workers = max_workers
        self.is_from_running_loop = ContextVar("Adapter_", default=False)


def _construct_all():
    """ Get or create new event loop """
    loop = take_event_loop()
    executor = AdaptiveExecutor()
    loop.set_default_executor(executor)
    return loop, executor


def _on_shutdown(executor, loop):
    """ Do some cleanup """
    if not executor.is_from_running_loop.get():
        loop.call_soon_threadsafe(_stop_loop, loop)
    executor.shutdown(wait=True)


def sync(func, *args, **kwargs):
    """
    Function to execute async functions synchronously

    :param func: Async function, which you want to execute in synchronous code
    :param args: args, which need your async func
    :param kwargs: kwargs, which need your async func
    """

    # construct an event loop and executor
    loop, executor = _construct_all()
    # Run our coroutine thread safe
    wrapped_future = asyncio.run_coroutine_threadsafe(func(*args, **kwargs), loop=loop)
    # Run loop.run_forever(), but do it safely
    executor.submit(run_forever_safe, loop)
    try:
        # Get result
        return _await_sync(wrapped_future)
    finally:
        # Cleanup
        _on_shutdown(executor, loop)


def async_as_sync(func):
    """ Decorator, which use `sync` function to implement async to sync """

    @ft.wraps(func)
    def wrapper(*args, **kwargs):
        return sync(func, *args, **kwargs)

    return wrapper


def check_transaction(transactions, amount, transaction_type, sender, comment):
    for txn in transactions:
        if float(txn.sum.amount) >= amount:
            if txn.type == transaction_type:
                if txn.comment == comment and txn.to_account == sender:
                    return True
                elif comment and sender:
                    continue
                elif txn.to_account == sender:
                    return True
                elif sender:
                    continue
                elif txn.comment == comment:
                    return True
    return False


def parse_limits(response, model):
    limits = {}
    for code, limit in response.get("limits").items():
        if not limit:
            continue
        limits.update({code: model.parse_obj(limit[0])})
    return limits


class override_error_messages:  # NOQA
    def __init__(self, status_codes) -> None:
        self.status_codes = status_codes

    def __call__(self, func):
        status_codes = self.status_codes

        @ft.wraps(func)
        async def wrapper(*args, **kwargs):
            from glQiwiApi import RequestError

            try:
                return await func(*args, **kwargs)
            except RequestError as ex:
                if int(ex.status_code) in status_codes.keys():
                    error = status_codes.get(int(ex.status_code))
                    ex = RequestError(
                        message=error.get("message"),
                        status_code=ex.status_code,
                        traceback_info=error.get("json_info"),
                        additional_info=ex.additional_info,
                    )
                raise ex

        return wrapper


def check_api_method(api_method):
    if not isinstance(api_method, str):
        raise RuntimeError(
            f"Invalid type of api_method(must  be string)."
            f" Passed {type(api_method)}"
        )


def check_transactions_payload(
    data,
    records,
    operation_types=None,
    start_date=None,
    end_date=None,
    start_record=None,
):
    from glQiwiApi import InvalidData

    if records <= 0 or records > 100:
        raise InvalidData(
            "Неверное количество записей. "
            "Кол-во записей, которые можно запросить,"
            " находиться в диапазоне от 1 до 100 включительно"
        )
    if operation_types:
        if all(
            isinstance(operation_type, OperationType)
            for operation_type in operation_types
        ):
            op_types = [operation_type.value for operation_type in operation_types]
            data.update({"type": " ".join(op_types)})

    if isinstance(start_record, int):
        if start_record < 0:
            raise InvalidData("Укажите позитивное число")
        data.update({"start_record": start_record})

    if start_date:
        if not isinstance(start_date, datetime.datetime):
            raise InvalidData(
                "Параметр start_date был передан неправильным типом данных"
            )
        data.update({"from": datetime_to_str_in_iso(start_date, yoo_money_format=True)})

    if end_date:
        if not isinstance(end_date, datetime.datetime):
            raise InvalidData("Параметр end_date был передан неправильным типом данных")
        data.update({"till": datetime_to_str_in_iso(end_date, yoo_money_format=True)})
    return data


def check_dates_for_statistic_request(start_date, end_date):
    first_expression = isinstance(start_date, datetime.datetime) and isinstance(
        end_date, datetime.datetime
    )
    second_expression = isinstance(start_date, datetime.timedelta) and isinstance(
        end_date, datetime.timedelta
    )
    if first_expression or second_expression:
        delta: datetime.timedelta = end_date - start_date
        if delta.days > 90:
            raise ValueError(
                "Максимальный период для выгрузки" " статистики - 90 календарных дней."
            )
    else:
        raise ValueError(
            "Вы передали значения начальной " "и конечной даты в неправильном формате."
        )


async def save_file(dir_path, file_name, data):
    """
    Saving file in dir_path/file_name.pdf with some data

    :param dir_path:
    :param file_name:
    :param data:
    """
    if dir_path is None and file_name is None:
        return data

    if isinstance(dir_path, str):
        dir_path = pathlib.Path(dir_path)

    if not dir_path.is_dir():
        raise TypeError("Invalid path to save, its not directory!")

    path_to_file: pathlib.Path = dir_path / (file_name + ".pdf")
    async with aiofiles.open(path_to_file, "wb") as file:
        return await file.write(data)
