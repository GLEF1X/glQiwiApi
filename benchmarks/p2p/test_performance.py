# pip install pytest-benchmark
import os

import pytest
from pyqiwip2p.AioQiwip2p import AioQiwiP2P
from pytest_benchmark.fixture import BenchmarkFixture

from glQiwiApi import QiwiP2PClient

wrapper = QiwiP2PClient(secret_p2p=os.getenv("SECRET_P2P"))

c = AioQiwiP2P(auth_key=os.getenv("SECRET_P2P"))


# Results on my machine (smaller is better)
# test_create_bill_with_glQiwiApi      90.9925 (1.0)      103.3993 (1.0)       95.4082 (1.0)      5.3941 (1.0)       92.4023 (1.0)       8.2798 (1.0)           1;0  10.4813 (1.0)           5          11
# test_create_bill_with_pyQiwiP2P     112.2819 (1.23)     135.0227 (1.31)     123.7498 (1.30)     9.9919 (1.85)     127.5926 (1.38)     17.2723 (2.09)          2;0   8.0808 (0.77)          5          10


async def create_bill_with_glQiwiApi():
    await wrapper.create_p2p_bill(amount=1)


async def create_bill_with_pyQiwiP2P():
    await c.bill(amount=1)


@pytest.fixture()
def aio_benchmark(benchmark: BenchmarkFixture) -> BenchmarkFixture:
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
async def test_create_bill_with_glQiwiApi(aio_benchmark: BenchmarkFixture) -> None:
    @aio_benchmark
    async def _():
        await create_bill_with_glQiwiApi()


@pytest.mark.asyncio
async def test_create_bill_with_pyQiwiP2P(aio_benchmark: BenchmarkFixture) -> None:
    @aio_benchmark
    async def _():
        await create_bill_with_pyQiwiP2P()
