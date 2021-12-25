# pip install pytest-benchmark

import pytest
from pyqiwip2p.AioQiwip2p import AioQiwiP2P

from glQiwiApi import QiwiWrapper

wrapper = QiwiWrapper(secret_p2p="")

c = AioQiwiP2P(auth_key="")


# Results on my machine (smaller is better)
# test_create_bill_with_glQiwiApi      86.0165 (1.0)      114.0327 (1.0)       96.9864 (1.0)      10.9067 (1.0)       92.9798 (1.0)      16.2909 (1.62)          3;0  10.3107 (1.0)           7           1
# test_create_bill_with_pyQiwiP2P     105.5675 (1.23)     139.7492 (1.23)     118.8386 (1.23)     12.6030 (1.16)     115.7287 (1.24)     10.0607 (1.0)           2;1   8.4148 (0.82)          5           1


async def create_bill_with_glQiwiApi():
    await wrapper.create_p2p_bill(amount=1)


async def create_bill_with_pyQiwiP2P():
    await c.bill(amount=1)


@pytest.fixture()
def aio_benchmark(benchmark):
    import asyncio
    import threading

    class Sync2Async:
        def __init__(self, coro, *args, **kwargs):
            self.coro = coro
            self.args = args
            self.kwargs = kwargs
            self.custom_loop = None
            self.thread = None

        def start_background_loop(self) -> None:
            asyncio.set_event_loop(self.custom_loop)
            self.custom_loop.run_forever()

        def __call__(self):
            evloop = None
            awaitable = self.coro(*self.args, **self.kwargs)
            try:
                evloop = asyncio.get_running_loop()
            except:
                pass
            if evloop is None:
                return asyncio.run(awaitable)
            else:
                if not self.custom_loop or not self.thread or not self.thread.is_alive():
                    self.custom_loop = asyncio.new_event_loop()
                    self.thread = threading.Thread(target=self.start_background_loop, daemon=True)
                    self.thread.start()

                return asyncio.run_coroutine_threadsafe(awaitable, self.custom_loop).result()

    def _wrapper(func, *args, **kwargs):
        if asyncio.iscoroutinefunction(func):
            benchmark(Sync2Async(func, *args, **kwargs))
        else:
            benchmark(func, *args, **kwargs)

    return _wrapper


@pytest.mark.asyncio
async def test_create_bill_with_glQiwiApi(aio_benchmark):
    @aio_benchmark
    async def _():
        await create_bill_with_glQiwiApi()


@pytest.mark.asyncio
async def test_create_bill_with_pyQiwiP2P(aio_benchmark):
    @aio_benchmark
    async def _():
        await create_bill_with_pyQiwiP2P()
