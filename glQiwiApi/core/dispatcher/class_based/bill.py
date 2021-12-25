from __future__ import annotations

import abc
from typing import Optional

from glQiwiApi.core.dispatcher.class_based.base import ClientMixin, Handler
from glQiwiApi.base_types.amount import PlainAmount
from glQiwiApi.qiwi.types.bill import Bill


class AbstractBillHandler(Handler[Bill], ClientMixin[Bill], abc.ABC):
    @property
    def bill_id(self) -> str:
        return self.event.id

    @property
    def bill_sum(self) -> PlainAmount:
        return self.event.amount

    @property
    def pay_url(self) -> Optional[str]:
        return self.event.pay_url
