from typing import Union, Optional, Type, Any

from glQiwiApi.core.dispatcher.filters import BaseFilter
from glQiwiApi.types import Transaction, TransactionWebhook, BillWebhook


class TransactionFilter(BaseFilter[Transaction]):
    async def check(self, update: Union[Transaction, TransactionWebhook]) -> bool:
        return isinstance(update, (TransactionWebhook, Transaction))


class BillFilter(BaseFilter[BillWebhook]):
    async def check(self, update: BillWebhook) -> bool:
        return isinstance(update, BillWebhook)


class ErrorFilter(BaseFilter[Exception]):
    def __init__(self, exception: Optional[Union[Type[Exception], Exception]] = None):
        self.exception: Union[Type[Exception], Exception] = exception or Exception

    async def check(self, error: Union[Type[Exception], Exception], *args: Any) -> bool:
        try:
            raise error
        except self.exception:  # type: ignore
            return True
        except:  # noqa
            raise error
