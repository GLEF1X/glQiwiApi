import asyncio
import logging

import pytest

from glQiwiApi import QiwiMaps, types, async_as_sync
from glQiwiApi.utils.decorators import measure_time

LOGGER = logging.getLogger(__name__)


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
        await asyncio.sleep(0.1)
        result += 1

    my_async_func()
    assert result == 1


def test_async_as_sync_with_callback(maps_client: QiwiMaps):
    @async_as_sync()
    async def callback():
        await maps_client.close()

    @async_as_sync(async_shutdown_callback=callback)
    async def my_async_func():
        async with maps_client:
            partners = await maps_client.partners()
        assert all(isinstance(p, types.Partner) for p in partners)

    my_async_func()


@pytest.mark.asyncio
async def test_measure_time(caplog):
    async def func():
        await asyncio.sleep(0.1)

    with caplog.at_level(logging.INFO):
        await measure_time(LOGGER).__call__(func)()

    assert "Function `func` executed for" in caplog.text
