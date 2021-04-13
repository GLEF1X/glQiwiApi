import functools as ft
import re
import time
import warnings
from dataclasses import is_dataclass
from datetime import datetime
from typing import Optional, Union, Type

import pytz
from pydantic import ValidationError
from pytz.reference import LocalTimezone

try:
    import orjson
except (ModuleNotFoundError, ImportError):
    warnings.warn(
        'You should install orjson module to improve performance.',
        ResourceWarning
    )
    import json as orjson

Local = LocalTimezone()


def measure_time(func):
    """
    Декоратор для замера времени выполнения функции
    """

    @ft.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.monotonic()
        await func(*args, **kwargs)
        print(f'Executed for {time.monotonic() - start_time} secs')

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
    return obj.isoformat(' ').replace(" ", "T") + re.findall(pattern, local_date)[0]


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


def format_objects(iterable_obj, obj, transfers=None):
    """
    Функция для форматирования объектов, которые приходят от апи
    """
    kwargs = {}
    objects = []
    for transaction in iterable_obj:
        for key, value in transaction.items():
            if key in obj.__dict__.get(
                    '__annotations__').keys() or key in transfers.keys():
                try:
                    fill_key = key if not transfers.get(key) else transfers.get(
                        key)
                except AttributeError:
                    fill_key = key
                sp_obj: Optional[Union[str, Type]] = obj.__dict__.get(
                    '__annotations__').get(fill_key)
                if is_dataclass(sp_obj):
                    try:
                        kwargs.update({fill_key: sp_obj(**value)})
                    except TypeError:
                        kwargs.update({fill_key: sp_obj(
                            **format_objects_for_fill(value, transfers))})
                    continue
                kwargs.update({fill_key: value})
        objects.append(obj(**kwargs))
        kwargs = {}
    return objects


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
    import json
    return json.loads(json.dumps(data))


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
