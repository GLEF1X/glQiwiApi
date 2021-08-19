from __future__ import annotations

import abc
from typing import Optional

from glQiwiApi.types import WebHook
from glQiwiApi.types.qiwi_types.webhooks import WebhookPayment
from .base import Handler, ClientMixin


class AbstractWebHookHandler(Handler[WebHook], ClientMixin[WebHook], abc.ABC):
    @property
    def hook_id(self) -> str:
        return self.event.hook_id

    @property
    def payment(self) -> Optional[WebhookPayment]:
        return self.event.payment
