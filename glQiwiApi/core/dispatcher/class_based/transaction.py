from __future__ import annotations

import abc

from glQiwiApi.types import Transaction, Sum
from .base import Handler, ClientMixin


class AbstractTransactionHandler(Handler[Transaction], ClientMixin[Transaction], abc.ABC):

    @property
    def txn_id(self) -> int:
        return self.event.id

    @property
    def txn_sum(self) -> Sum:
        return self.event.sum
