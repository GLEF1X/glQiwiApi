import asyncio
from concurrent.futures import ThreadPoolExecutor

from build.lib.glQiwiApi import QiwiWrapper, sync
from build.lib.glQiwiApi.utils.basics import sync_measure_time
from glQiwiApi.utils.basics import measure_time
#
# y = YooMoneyAPI()
#
# y.build_url_for_auth()  # выдаст ошибку
#
# YooMoneyAPI.build_url_for_auth()  # ошибки нет, однако методом мы пользуемся

wallet = QiwiWrapper(TOKEN, WALLET, cache_time=10, without_context=True)


async def main3():
    await asyncio.sleep(0.1)
    print("EXECUTED")


# @measure_time
# async def main():
#     async with wallet as w:
#         print(await w.account_info())

@sync_measure_time
def main():
    print(sync(wallet.get_balance))


main()

# asyncio.run(main())


class AdaptiveExecutor(ThreadPoolExecutor):
    def __init__(self, max_workers=None, **kwargs):
        super().__init__(max_workers, 'sync_adapter_', **kwargs)
        self.max_workers = max_workers


def _construct_event_loop():
    """ Get or create new event loop """
    try:
        loop = asyncio.get_running_loop()
        if loop.is_closed() or not loop:
            raise RuntimeError()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    loop.set_debug(True)
    executor = AdaptiveExecutor()
    loop.set_default_executor(executor)
    return loop, executor
