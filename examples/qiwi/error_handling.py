import logging
from typing import Any

from glQiwiApi import QiwiWrapper
from glQiwiApi.utils import executor

api_access_token = "your token"
phone_number = "your number"

wallet = QiwiWrapper(api_access_token=api_access_token, phone_number=phone_number)
logger = logging.getLogger(__name__)


@wallet.error_handler(exception=OSError)
async def os_error_handler(exception: Exception, *args: Any) -> None:
    # do something here, if exception has occurred, for example log it
    logger.exception("Exception %s occurred. WTF!!!", exception)


executor.start_polling(wallet)
