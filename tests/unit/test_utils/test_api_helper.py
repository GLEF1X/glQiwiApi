import asyncio

import pytest

from glQiwiApi import QiwiMaps
from glQiwiApi.utils.synchronous import async_as_sync
from glQiwiApi.qiwi.clients.wallet.types import Partner


@pytest.fixture(name="maps_client", scope="function")
def maps_client():
    return QiwiMaps()


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
        partners = await maps_client.partners()
        assert all(isinstance(p, Partner) for p in partners)

    my_async_func()
