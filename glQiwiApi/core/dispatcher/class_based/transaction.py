from __future__ import annotations

import abc

from glQiwiApi.base_types import AmountWithCurrency
from glQiwiApi.qiwi.types import Transaction
from .base import ClientMixin, Handler


class AbstractTransactionHandler(Handler[Transaction], ClientMixin[Transaction], abc.ABC):
    @property
    def transaction_id(self) -> int:
        return self.event.id

    @property
    def transaction_sum(self) -> AmountWithCurrency:
        return self.event.sum
