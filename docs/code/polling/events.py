from glQiwiApi import QiwiWallet
from glQiwiApi.core.event_fetching import executor
from glQiwiApi.core.event_fetching.dispatcher import QiwiDispatcher
from glQiwiApi.core.event_fetching.executor import HandlerContext
from glQiwiApi.qiwi.clients.wallet.types import Transaction

qiwi_dp = QiwiDispatcher()
wallet = QiwiWallet(api_access_token='token', phone_number='+phone number')


@qiwi_dp.transaction_handler()
async def handle_transaction(t: Transaction, ctx: HandlerContext):
    """Handle transaction here"""
    ctx.wallet  # this way you can use QiwiWallet instance to avoid global variables


async def on_startup(ctx: HandlerContext):
    ctx.wallet  # do something here


async def on_shutdown(ctx: HandlerContext):
    pass


if __name__ == '__main__':
    executor.start_polling(wallet, qiwi_dp, on_startup=on_startup, on_shutdown=on_shutdown)
