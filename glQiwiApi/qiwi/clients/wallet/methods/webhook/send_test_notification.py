from typing import Dict, Any, ClassVar

from glQiwiApi.qiwi.base import QiwiAPIMethod


class SendTestWebhookNotification(QiwiAPIMethod[Dict[Any, Any]]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://edge.qiwi.com/payment-notifier/v1/hooks/test"
