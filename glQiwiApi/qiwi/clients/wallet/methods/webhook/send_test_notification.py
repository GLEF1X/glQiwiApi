from typing import Dict, Any, ClassVar

from glQiwiApi.base.api_method import APIMethod


class SendTestWebhookNotification(APIMethod[Dict[Any, Any]]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://edge.qiwi.com/payment-notifier/v1/hooks/test"
