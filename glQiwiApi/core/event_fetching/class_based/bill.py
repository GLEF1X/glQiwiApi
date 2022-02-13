from __future__ import annotations

import abc
from typing import TYPE_CHECKING, cast

from glQiwiApi.core.event_fetching.class_based.base import Handler
from glQiwiApi.qiwi.clients.p2p.types import Bill
from glQiwiApi.types.amount import PlainAmount

if TYPE_CHECKING:
    from glQiwiApi.qiwi.clients.p2p.client import QiwiP2PClient


class AbstractBillHandler(Handler[Bill], abc.ABC):
    @property
    def wallet(self) -> QiwiP2PClient:
        return cast(QiwiP2PClient, self.context["wallet"])

    @property
    def bill_id(self) -> str:
        return self.event.id

    @property
    def bill_sum(self) -> PlainAmount:
        return self.event.amount

    @property
    def pay_url(self) -> str:
        return self.event.pay_url

    @property
    def shim_url(self) -> str:
        return self.wallet.create_shim_url(self.event.invoice_uid)
