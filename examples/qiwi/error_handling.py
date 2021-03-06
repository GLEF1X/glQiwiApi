from __future__ import annotations

from typing import Any

from glQiwiApi import QiwiWrapper
from glQiwiApi.utils import executor

api_access_token = "your token"
phone_number = "your number"

wallet = QiwiWrapper(api_access_token=api_access_token, phone_number=phone_number)


@wallet.error_handler(exception=OSError)
async def os_error_handler(exception: Exception, *args: Any) -> None:
    # do something here, if exception has occurred, for example log it
    wallet.logger.exception("Exception %s occurred. WTF!!!", exception)


executor.start_polling(wallet, skip_updates=True)
