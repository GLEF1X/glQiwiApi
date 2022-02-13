from typing import ClassVar, Any

from pydantic import Field

from glQiwiApi.core.abc.api_method import Request
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import WebhookInfo


class RegisterWebhook(QiwiAPIMethod[WebhookInfo]):
    url: ClassVar[str] = "https://edge.qiwi.com/payment-notifier/v1/hooks"
    http_method: ClassVar[str] = "PUT"

    webhook_url: str = Field(..., alias="param")
    txn_type: int = Field(..., alias="txnType")

    hook_type: int = Field(default=1, alias="hookType")

    def build_request(self, **url_format_kw: Any) -> "Request":
        return Request(
            endpoint=self.url.format(**url_format_kw),
            params=self.dict(by_alias=True),
            http_method=self.http_method,
        )
