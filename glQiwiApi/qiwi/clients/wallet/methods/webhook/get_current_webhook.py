from typing import ClassVar



from glQiwiApi.base.api_method import APIMethod
from glQiwiApi.qiwi.clients.wallet.types import WebhookInfo


class GetCurrentWebhook(APIMethod[WebhookInfo]):
    url: ClassVar[str] = "https://edge.qiwi.com/payment-notifier/v1/hooks/active"
    http_method: ClassVar[str] = "GET"
