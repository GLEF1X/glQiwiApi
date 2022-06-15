from typing import Any, ClassVar, Dict

from glQiwiApi.qiwi.base import QiwiAPIMethod


class SendTestWebhookNotification(QiwiAPIMethod[Dict[Any, Any]]):
    http_method: ClassVar[str] = 'GET'
    url: ClassVar[str] = 'https://edge.qiwi.com/payment-notifier/v1/hooks/test'
