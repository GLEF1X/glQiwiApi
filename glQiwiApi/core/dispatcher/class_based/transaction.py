from __future__ import annotations

import abc
from typing import TYPE_CHECKING

from glQiwiApi.base.types.amount import AmountWithCurrency
from glQiwiApi.qiwi.clients.wallet.types.transaction import Transaction
from .base import Handler

if TYPE_CHECKING:
    from glQiwiApi.qiwi.clients.wallet import QiwiWallet


class AbstractTransactionHandler(Handler[Transaction], abc.ABC):

    @property
    def wallet(self) -> QiwiWallet:
        return self.context["wallet"]

    @property
    def transaction_id(self) -> int:
        return self.event.id

    @property
    def transaction_sum(self) -> AmountWithCurrency:
        return self.event.sum
