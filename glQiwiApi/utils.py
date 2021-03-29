import re
import time
from datetime import datetime
from typing import TypeVar, Callable, Any
import functools as ft
from pytz.reference import Local

F = TypeVar('F', bound=Callable[..., Any])


def measure_time(func: F):
    @ft.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.monotonic()
        await func(*args, **kwargs)
        print(f'Executed for {time.monotonic() - start_time} secs')

    return wrapper


def datetime_to_str_in_iso(obj: datetime) -> str:
    return obj.isoformat(' ').replace(" ", "T") + re.findall(r'[+]\d{2}[:]\d{2}', str(datetime.now(tz=Local)))[0]
