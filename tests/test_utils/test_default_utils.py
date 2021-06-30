import asyncio
from datetime import datetime

from glQiwiApi.utils.api_helper import async_as_sync, to_datetime


def test_async_as_sync():
    result = 0

    @async_as_sync
    async def my_async_func():
        nonlocal result
        await asyncio.sleep(0.5)
        result += 1

    my_async_func()
    assert result == 1


def test_to_datetime_util():
    datetime_as_string: str = "2021-06-02 15:07:55"

    assert isinstance(to_datetime(datetime_as_string), datetime)
