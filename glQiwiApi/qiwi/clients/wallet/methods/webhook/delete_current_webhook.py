from typing import ClassVar, Any, Dict

from glQiwiApi.base.api_method import APIMethod, Request


class DeleteWebhook(APIMethod[Dict[Any, Any]]):
    url: ClassVar[str] = "https://edge.qiwi.com/payment-notifier/v1/hooks/{hook_id}"
    http_method: ClassVar[str] = "DELETE"

    hook_id: str

    def build_request(self, **url_format_kw: Any) -> Request:
        return super().build_request(**url_format_kw, hook_id=self.hook_id)
