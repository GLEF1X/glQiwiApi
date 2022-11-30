from glQiwiApi import QiwiWallet
from glQiwiApi.core.event_fetching import executor
from glQiwiApi.core.event_fetching.dispatcher import QiwiDispatcher
from glQiwiApi.core.event_fetching.executor import HandlerContext
from glQiwiApi.core.event_fetching.filters import ExceptionFilter
from glQiwiApi.qiwi.clients.wallet.types import Transaction
from glQiwiApi.qiwi.exceptions import QiwiAPIError

qiwi_dp = QiwiDispatcher()
wallet = QiwiWallet(api_access_token='token', phone_number='+phone number')


@qiwi_dp.transaction_handler()
async def handle_transaction(t: Transaction, ctx: HandlerContext):
    """Handle transaction here"""
    ctx.wallet  # this way you can use QiwiWallet instance to avoid global variables


@qiwi_dp.exception_handler(ExceptionFilter(QiwiAPIError))
async def handle_exception(err: QiwiAPIError, ctx: HandlerContext):
    pass


if __name__ == '__main__':
    executor.start_polling(wallet, qiwi_dp)
