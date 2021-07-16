from glQiwiApi import types
from glQiwiApi.core.web_hooks.dispatcher import Dispatcher

dp = Dispatcher()


async def handler(event: types.Notification) -> int:
    return 2


dp.register_bill_handler(handler)
