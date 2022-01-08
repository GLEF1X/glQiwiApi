import logging

from glQiwiApi import QiwiWallet
from glQiwiApi.qiwi.types import Transaction
from glQiwiApi.utils import executor

api_access_token = "your token"
phone_number = "your number"

wallet = QiwiWallet(api_access_token=api_access_token, phone_number=phone_number)

logger = logging.getLogger(__name__)


@wallet.transaction_handler()
async def my_first_handler(update: Transaction):
    assert isinstance(update, Transaction)


def on_startup(wrapper: QiwiWallet):
    logger.info("This message logged on startup")


executor.start_polling(wallet, on_startup=on_startup)
