import time
from typing import ClassVar, Any, Dict

from pydantic import Field

from glQiwiApi.core.abc.api_method import RuntimeValue
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types.payment_info import PaymentInfo


class BuyQIWIMasterPackage(QiwiAPIMethod[PaymentInfo]):
    url: ClassVar[str] = "https://edge.qiwi.com/sinap/api/v2/terms/28004/payments"
    http_method: ClassVar[str] = "POST"

    json_payload_schema: ClassVar[Dict[str, Any]] = {
        "id": RuntimeValue(default_factory=lambda: str(int(time.time() * 1000))),
        "sum": {"amount": RuntimeValue(default=2999), "currency": "643"},
        "paymentMethod": {"type": "Account", "accountId": "643"},
        "comment": "Оплата",
        "fields": {"account": RuntimeValue(), "vas_alias": "qvc-master"},
    }

    phone_number: str = Field(..., scheme_path="fields.account")
