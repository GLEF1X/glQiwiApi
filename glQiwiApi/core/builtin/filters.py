from typing import Union

from glQiwiApi.core.web_hooks.filter import BaseFilter
from glQiwiApi.types import Transaction, WebHook, Notification


class TransactionFilter(BaseFilter[Transaction]):
    async def check(self, update: Union[Transaction, WebHook]) -> bool:
        return isinstance(update, (WebHook, Transaction))


class BillFilter(BaseFilter[Notification]):
    async def check(self, update: Notification) -> bool:
        return isinstance(update, Notification)
