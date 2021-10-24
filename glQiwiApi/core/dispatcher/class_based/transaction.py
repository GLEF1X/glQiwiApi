from __future__ import annotations

import abc

from glQiwiApi.types import Transaction, CurrencyAmount
from .base import Handler, ClientMixin


class AbstractTransactionHandler(
    Handler[Transaction], ClientMixin[Transaction], abc.ABC
):
    @property
    def transaction_id(self) -> int:
        return self.event.id

    @property
    def transaction_sum(self) -> CurrencyAmount:
        return self.event.sum
