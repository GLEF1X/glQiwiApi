import logging

from glQiwiApi import QiwiWrapper, base_types
from glQiwiApi.utils import executor

api_access_token = "your token"
phone_number = "your number"

wallet = QiwiWrapper(api_access_token=api_access_token, phone_number=phone_number)

logger = logging.getLogger(__name__)


@wallet.transaction_handler()
async def my_first_handler(update: base_types.Transaction):
    assert isinstance(update, base_types.Transaction)


def on_startup(wrapper: QiwiWrapper):
    logger.info("This message logged on startup")


executor.start_polling(wallet, on_startup=on_startup)
