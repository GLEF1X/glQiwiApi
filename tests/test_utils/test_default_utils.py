import asyncio
from datetime import datetime

import pytest

from glQiwiApi import QiwiMaps, types
from glQiwiApi.utils.api_helper import async_as_sync, to_datetime


@pytest.fixture(name="maps_client", scope="function")
@pytest.mark.asyncio
async def maps_client():
    maps = QiwiMaps()
    yield maps


def test_async_as_sync():
    result = 0

    @async_as_sync()
    async def my_async_func():
        nonlocal result
        await asyncio.sleep(0.5)
        result += 1

    my_async_func()
    assert result == 1


def test_async_as_sync_with_callback(maps_client: QiwiMaps):
    @async_as_sync()
    async def callback():
        await maps_client.close()

    @async_as_sync(shutdown_callback=callback)
    async def my_async_func():
        partners = await maps_client.partners()
        assert all(isinstance(p, types.Partner) for p in partners)

    my_async_func()


def test_to_datetime_util():
    datetime_as_string: str = "2021-06-02 15:07:55"

    assert isinstance(to_datetime(datetime_as_string), datetime)
