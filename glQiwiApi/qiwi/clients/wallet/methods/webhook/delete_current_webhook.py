from typing import Any, ClassVar, Dict

from glQiwiApi.core.abc.api_method import Request
from glQiwiApi.qiwi.base import QiwiAPIMethod


class DeleteWebhook(QiwiAPIMethod[Dict[Any, Any]]):
    url: ClassVar[str] = 'https://edge.qiwi.com/payment-notifier/v1/hooks/{hook_id}'
    http_method: ClassVar[str] = 'DELETE'

    hook_id: str

    def build_request(self, **url_format_kw: Any) -> Request:
        return super().build_request(**url_format_kw, hook_id=self.hook_id)
