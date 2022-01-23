from __future__ import annotations

import abc
from typing import Optional

from glQiwiApi.qiwi.clients.wallet.types.webhooks import TransactionWebhook, WebhookPayment
from .base import Handler


class AbstractTransactionWebhookHandler(Handler[TransactionWebhook], abc.ABC):
    @property
    def hook_id(self) -> str:
        return self.event.id

    @property
    def payment(self) -> Optional[WebhookPayment]:
        return self.event.payment
