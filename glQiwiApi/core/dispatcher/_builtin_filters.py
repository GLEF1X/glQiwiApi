from typing import Union, Optional, Type, Any

from glQiwiApi.core.dispatcher.filters import BaseFilter
from glQiwiApi.types import Transaction, WebHook, Notification


class TransactionFilter(BaseFilter[Transaction]):
    async def check(self, update: Union[Transaction, WebHook]) -> bool:
        return isinstance(update, (WebHook, Transaction))


class BillFilter(BaseFilter[Notification]):
    async def check(self, update: Notification) -> bool:
        return isinstance(update, Notification)


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
