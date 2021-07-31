from __future__ import annotations

import abc
from typing import Optional

from glQiwiApi.core.dispatcher.class_based.base import Handler, ClientMixin
from glQiwiApi.types import Bill, OptionalSum


class AbstractBillHandler(Handler[Bill], ClientMixin[Bill], abc.ABC):

    @property
    def bill_id(self) -> str:
        return self.event.bill_id

    @property
    def bill_sum(self) -> OptionalSum:
        return self.event.amount

    @property
    def pay_url(self) -> Optional[str]:
        return self.event.pay_url
