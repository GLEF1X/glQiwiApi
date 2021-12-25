from __future__ import annotations

import abc
from typing import Optional

from glQiwiApi.qiwi.types import TransactionWebhook
from glQiwiApi.qiwi.types.webhooks import WebhookPayment
from .base import ClientMixin, Handler


class AbstractTransactionWebhookHandler(
    Handler[TransactionWebhook], ClientMixin[TransactionWebhook], abc.ABC
):
    @property
    def hook_id(self) -> str:
        return self.event.id

    @property
    def payment(self) -> Optional[WebhookPayment]:
        return self.event.payment
