import asyncio
import base64
import binascii
import concurrent.futures as futures
import datetime
import functools as ft
import hashlib
import hmac
import re
import time
from contextvars import ContextVar
from copy import deepcopy

import pytz
from pydantic import ValidationError, BaseModel
from pytz.reference import LocalTimezone

try:
    import orjson
except (ModuleNotFoundError, ImportError):
    import json as orjson

# Gets your local time zone
Local = LocalTimezone()

QIWI_MASTER = {
    "id": str(int(time.time() * 1000)),
    "sum": {
        "amount": 2999,
        "currency": "643"
    },
    "paymentMethod": {
        "type": "Account",
        "accountId": "643"
    },
    "comment": "test",
    "fields": {
        "account": "",
        "vas_alias": "qvc-master"
    }
}


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
        print(
            f'Function `{func.__name__}` executed for {execute_time} secs')
        return result

    return wrapper


def datetime_to_str_in_iso(obj, yoo_money_format=False):
    """
    Converts a date to a standard format for API's

    :param obj: datetime object to parse to string
    :param yoo_money_format: boolean
    :return: string - parsed date
    """
    if not isinstance(obj, datetime.datetime):
        return ''
    if yoo_money_format:
        # Приводим время к UTC,
        # так как yoomoney апи принимает именно в таком формате
        return pytz.utc.localize(obj).replace(tzinfo=None).isoformat(
            ' ').replace(" ", "T") + "Z"
    local_date = str(datetime.datetime.now(tz=Local))
    pattern = re.compile(r'[+]\d{2}[:]\d{2}')
    from_pattern = re.findall(pattern, local_date)[0]
    return obj.isoformat(' ').replace(" ", "T") + from_pattern


def parse_auth_link(response_data):
    """
    Parse link for getting code, which needs to be entered in the method
    get_access_token

    :param response_data:
    """
    regexp = re.compile(
        r'https://yoomoney.ru/oauth2/authorize[?]requestid[=]\w+'
    )
    return re.findall(regexp, str(response_data))[0]


def check_dates(start_date, end_date, payload_data):
    """ Check correctness of transferred dates and add it to request """
    if isinstance(
            start_date, (datetime.datetime, datetime.timedelta)
    ) and isinstance(
        end_date, (datetime.datetime, datetime.timedelta)
    ):
        if (end_date - start_date).total_seconds() > 0:
            payload_data.update(
                {
                    'startDate': datetime_to_str_in_iso(
                        start_date
                    ),
                    'endDate': datetime_to_str_in_iso(
                        end_date
                    )
                }
            )
        else:
            raise Exception(
                'end_date не может быть больше чем start_date'
            )
    return payload_data


def parse_commission_request_payload(
        default_data,
        auth_maker,
        pay_sum,
        to_account
):
    """Set commission payload"""
    payload = deepcopy(default_data)
    payload.headers = auth_maker(payload.headers)
    payload.json['purchaseTotals']['total']['amount'] = pay_sum
    payload.json['account'] = to_account
    return payload, "99" if len(to_account) <= 15 else None


def parse_card_data(
        default_data,
        trans_sum,
        to_card,
        auth_maker,
):
    """Set card data payload"""
    data = deepcopy(default_data)
    data.json['sum']['amount'] = trans_sum
    data.json['fields']['account'] = to_card
    data.headers = auth_maker(headers=data.headers)
    return data


def parse_headers(content_json=False, auth=False):
    """
    Функция для добавления некоторых заголовков в запрос
    """
    headers = {
        'Host': 'yoomoney.ru',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    if content_json:
        headers.update(
            {'Accept': 'application/json'}
        )
    if auth:
        headers.update(
            {'Authorization': 'Bearer {token}'}
        )
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
    data.json['sum']['amount'] = str(trans_sum)
    data.json['sum']['currency'] = currency
    data.json['fields']['account'] = to_number
    data.json['comment'] = comment
    data.headers.update({'User-Agent': 'Android v3.2.0 MKT'})
    return data


def set_data_p2p_create(wrapped_data, amount, life_time, comment, theme_code,
                        pay_source_filter):
    """
    Setting data for p2p form creation transfer

    :param wrapped_data:
    :param amount:
    :param life_time:
    :param comment:
    :param theme_code:
    :param pay_source_filter:
    """
    wrapped_data.json['amount']['value'] = str(amount)
    wrapped_data.json['comment'] = comment
    wrapped_data.json['expirationDateTime'] = life_time
    if pay_source_filter in ['qw', 'card', 'mobile']:
        wrapped_data.json['customFields'][
            'paySourcesFilter'] = pay_source_filter
    if isinstance(theme_code, str):
        wrapped_data.json['customFields']['theme_code'] = theme_code
    if not isinstance(theme_code, str) and pay_source_filter not in [
        'qw',
        'card',
        'mobile'
    ]:
        wrapped_data.json.pop('customFields')
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
                objects.append(model.parse_raw(obj))
                continue
            for detached_obj in obj:
                objects.append(model.parse_raw(detached_obj))
        except ValidationError as ex:
            print(ex.json(indent=4))
    return objects


def simple_multiply_parse(lst_of_objects, model):
    """
    Parse simple objects, which cant raise ValidationError

    :param lst_of_objects: usually its response.response_data
    :param model: pydantic model, which will parse data
    """
    objects = []
    for obj in lst_of_objects:
        objects.append(model.parse_raw(obj))
    return objects


def hmac_key(key, amount, status, bill_id, site_id):
    """
    Функция расшифровки подписи webhook

    :param key: ключ webhook, закодированный в Base64
    :param amount: сумма p2p платежа
    :param status: статус платежа
    :param bill_id: unique p2p id
    :param site_id:
    """
    byte_key = binascii.unhexlify(key)
    invoice_params = (
        f"{amount.currency}|{amount.value}|{bill_id}|{site_id}|{status.value}"
    ).encode("utf-8")

    return hmac.new(
        byte_key, invoice_params, hashlib.sha256
    ).hexdigest().upper()


def hmac_for_transaction(
        webhook_key_base64,
        amount,
        txn_type,
        account,
        txn_id,
        txn_hash
):
    invoice_params = (
        f"{amount.currency}|{amount.amount}|{txn_type}|{account}|{txn_id}"
    )
    webhook_key = base64.b64decode(bytes(webhook_key_base64, 'utf-8'))
    return hmac.new(webhook_key, invoice_params.encode('utf-8'),
                    hashlib.sha256).hexdigest() == txn_hash


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


def allow_response_code(status_code):
    """
    Декоратор, который позволяет разрешить определенный код ответа от апи

    :param status_code: статус код, который будет рассмотрен как правильный,
     кроме 200
    """

    def wrap_func(func):
        async def wrapper(*args, **kwargs):
            from glQiwiApi import RequestError
            try:
                await func(*args, **kwargs)
            except RequestError as error:
                if error.status_code == str(status_code):
                    info = error.json_info
                    return {"success": True} if not info else info
                return {"success": False}

        return wrapper

    return wrap_func


def qiwi_master_data(ph_number):
    url = "https://edge.qiwi.com" + '/sinap/api/v2/terms/28004/payments'
    payload = deepcopy(QIWI_MASTER)
    payload["fields"]["account"] = ph_number
    return url, payload


def to_datetime(string_representation):
    """
    Вспомогательная функция для перевода строки во время

    :param string_representation: дата в виде строки
    :return: datetime representation
    """
    try:
        parsed = orjson.dumps(
            {'dt': string_representation}
        )
        return Parser.parse_raw(parsed).dt
    except (ValidationError, orjson.JSONDecodeError) as ex:
        return ex.json(indent=4)


def new_card_data(ph_number, order_id):
    payload = deepcopy(QIWI_MASTER)
    url = "https://edge.qiwi.com" + "/sinap/api/v2/terms/32064/payments"
    payload["fields"].pop("vas_alias")
    payload["fields"].update(order_id=order_id)
    payload["fields"]["account"] = ph_number
    return url, payload


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
        print(
            f'Function `{func.__name__}` executed for {execute_time} secs')
        return result

    return wrapper


def parse_amount(txn_type, txn):
    amount = txn.amount if txn_type == 'in' else txn.amount_due
    comment = txn.comment if txn_type == 'in' else txn.message
    return amount, comment


def check_params(amount_, amount, txn, transaction_type):
    if amount_ >= amount:
        if txn.direction == transaction_type:
            return True
    return False


def _run_forever_safe(loop) -> None:
    """ run a loop for ever and clean up after being stopped """

    loop.run_forever()
    # NOTE: loop.run_forever returns after calling loop.stop

    # -- cancel all tasks and close the loop gracefully

    loop_tasks_all = asyncio.all_tasks(loop=loop)

    for task in loop_tasks_all:
        task.cancel()
    # NOTE: `cancel` does not guarantee that the Task will be cancelled

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
        super().__init__(max_workers, 'sync_adapter_', **kwargs)
        self.max_workers = max_workers
        self.is_from_running_loop = ContextVar('Adapter_', default=False)


def _construct_all():
    """ Get or create new event loop """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
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
    Function to use async functions(libraries) synchronously

    :param func: Async function, which you want to execute in synchronous code
    :param args: args, which need your async func
    :param kwargs: kwargs, which need your async func
    """

    # construct an event loop and executor
    loop, executor = _construct_all()

    # Run our coroutine thread safe
    wrapped_future = asyncio.run_coroutine_threadsafe(
        func(*args, **kwargs),
        loop=loop
    )
    # Run loop.run_forever(), but do it safely
    executor.submit(_run_forever_safe, loop)
    try:
        # Get result
        return _await_sync(wrapped_future)
    finally:
        # Cleanup
        _on_shutdown(executor, loop)
