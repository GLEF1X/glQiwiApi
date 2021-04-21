import asyncio
import concurrent.futures as futures
import functools as ft
import re
import time
import warnings
from contextvars import ContextVar
from copy import deepcopy
from datetime import datetime

import pytz
from pydantic import ValidationError, BaseModel
from pytz.reference import LocalTimezone

try:
    import orjson
except (ModuleNotFoundError, ImportError):
    warnings.warn(
        'You should install orjson module to improve performance.',
        ResourceWarning
    )
    import json as orjson

# Локальная таймзона
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
    if not isinstance(obj, datetime):
        return ''
    if yoo_money_format:
        # Приводим время к UTC,
        # так как yoomoney апи принимает именно в таком формате
        return pytz.utc.localize(obj).replace(tzinfo=None).isoformat(
            ' ').replace(" ", "T") + "Z"
    local_date = str(datetime.now(tz=Local))
    pattern = re.compile(r'[+]\d{2}[:]\d{2}')
    from_pattern = re.findall(pattern, local_date)[0]
    return obj.isoformat(' ').replace(" ", "T") + from_pattern


def parse_auth_link(response_data):
    regexp = re.compile(
        r'https://yoomoney.ru/oauth2/authorize[?]requestid[=]\w+'
    )
    return re.findall(regexp, str(response_data))[0]


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


def format_objects_for_fill(data, transfers):
    for key, value in data.copy().items():
        if hasattr(transfers, 'get'):
            if key in transfers.keys():
                data.update({transfers.get(key): value})
                data.pop(key)
    return data


def set_data_to_wallet(data, to_number, trans_sum, comment, currency):
    data.json['sum']['amount'] = str(trans_sum)
    data.json['sum']['currency'] = currency
    data.json['fields']['account'] = to_number
    data.json['comment'] = comment
    data.headers.update({'User-Agent': 'Android v3.2.0 MKT'})
    return data


def set_data_p2p_create(wrapped_data, amount, life_time, comment, theme_code,
                        pay_source_filter):
    wrapped_data.json['amount']['value'] = str(amount)
    wrapped_data.json['comment'] = comment
    wrapped_data.json['expirationDateTime'] = life_time
    if pay_source_filter in ['qw', 'card', 'mobile']:
        wrapped_data.json['customFields'][
            'paySourcesFilter'] = pay_source_filter
    if isinstance(theme_code, str):
        wrapped_data.json['customFields']['theme_code'] = theme_code
    if not isinstance(theme_code, str) and pay_source_filter not in ['qw',
                                                                     'card',
                                                                     'mobile']:
        wrapped_data.json.pop('customFields')
    return wrapped_data.json


#
def multiply_objects_parse(lst_of_objects, model):
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
    objects = []
    for obj in lst_of_objects:
        objects.append(model.parse_raw(obj))
    return objects


def dump_response(func):
    """Декоратор, который гарантирует получения json данных в запросе"""

    @ft.wraps(func)
    async def wrapper(*args, **kwargs):
        kwargs.update({'get_json': True})
        return await func(*args, **kwargs)

    return wrapper


def custom_load(data):
    return orjson.loads(orjson.dumps(data))


class Parser(BaseModel):
    """ Модель pydantic для перевода строки в datetime """
    dt: datetime


def allow_response_code(status_code):
    """Декоратор, который позволяет разрешить определенный код ответа от апи"""

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
    if txn_type == 'in':
        amount = txn.amount
        comment = txn.comment
    else:
        amount = txn.amount_due
        comment = txn.message
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


def _await_sync(future, executor, loop):
    """ synchronously waits for a task """
    return future.result()


def _cancel_future(loop, future, executor) -> None:
    """ cancels future if any exception occurred """
    executor.submit(loop.call_soon_threadsafe, future.cancel)


def _stop_loop(loop) -> None:
    """ stops an event loop """
    loop.stop()


class AdaptiveExecutor(futures.ThreadPoolExecutor):
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
        return _await_sync(wrapped_future, executor=executor, loop=loop)
    finally:
        # Cleanup
        _on_shutdown(executor, loop)
