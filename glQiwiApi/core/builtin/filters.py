from typing import Any

from glQiwiApi.core.web_hooks.filter import BaseFilter
from glQiwiApi.types import Transaction, WebHook, Notification


class TransactionFilter(BaseFilter):
    async def check(self, update: Any) -> bool:
        return isinstance(update, (WebHook, Transaction))


class BillFilter(BaseFilter):
    async def check(self, update: Any) -> bool:
        return isinstance(update, Notification)
