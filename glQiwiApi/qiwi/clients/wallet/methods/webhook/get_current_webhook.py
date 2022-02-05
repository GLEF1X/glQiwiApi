from typing import ClassVar

from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import WebhookInfo


class GetCurrentWebhook(QiwiAPIMethod[WebhookInfo]):
    url: ClassVar[str] = "https://edge.qiwi.com/payment-notifier/v1/hooks/active"
    http_method: ClassVar[str] = "GET"
