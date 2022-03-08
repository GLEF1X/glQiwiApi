import asyncio

from glQiwiApi import QiwiMaps
from glQiwiApi.qiwi.clients.wallet.types import Partner
from glQiwiApi.utils.synchronous import async_as_sync


def test_async_as_sync():
    result = 0

    @async_as_sync()
    async def my_async_func():
        nonlocal result
        await asyncio.sleep(0.1)
        result += 1

    my_async_func()
    assert result == 1


def test_async_as_sync_with_callback():
    callback_visited = asyncio.Event()

    @async_as_sync()
    async def callback():
        callback_visited.set()

    @async_as_sync(async_shutdown_callback=callback)
    async def my_async_func():
        async with QiwiMaps() as maps:
            partners = await maps.partners()
            assert all(isinstance(p, Partner) for p in partners)

    my_async_func()
    assert callback_visited.is_set() is True
