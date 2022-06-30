from __future__ import annotations

import abc
from typing import TYPE_CHECKING, cast

from glQiwiApi.qiwi.clients.wallet.types.transaction import Transaction
from glQiwiApi.types.amount import Amount

from .base import Handler

if TYPE_CHECKING:
    from glQiwiApi.qiwi.clients.wallet.client import QiwiWallet


class AbstractTransactionHandler(Handler[Transaction], abc.ABC):
    @property
    def wallet(self) -> QiwiWallet:
        return cast(QiwiWallet, self.context['wallet'])

    @property
    def transaction_id(self) -> int:
        return self.event.id

    @property
    def transaction_sum(self) -> Amount:
        return self.event.sum
