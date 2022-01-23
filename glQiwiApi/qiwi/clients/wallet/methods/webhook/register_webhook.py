from typing import ClassVar

from pydantic import Field

from glQiwiApi.base.api_method import APIMethod
from glQiwiApi.qiwi.clients.wallet.types import WebhookInfo


class RegisterWebhook(APIMethod[WebhookInfo]):
    url: ClassVar[str] = "https://edge.qiwi.com/payment-notifier/v1/hooks"
    http_method: ClassVar[str] = "PUT"

    webhook_url: str = Field(..., alias="param")
    txn_type: int = Field(..., alias="txnType")

    hook_type: int = 1
