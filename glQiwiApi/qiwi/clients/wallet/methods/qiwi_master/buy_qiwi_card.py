import time
from typing import ClassVar, Dict, Any

from pydantic import Field

from glQiwiApi.core.abc.api_method import RuntimeValue
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types.qiwi_master import OrderDetails


class BuyQiwiMasterCard(QiwiAPIMethod[OrderDetails]):
    url: ClassVar[str] = "https://edge.qiwi.com/sinap/api/v2/terms/32064/payments"
    http_method: ClassVar[str] = "POST"

    json_payload_schema: ClassVar[Dict[str, Any]] = {
        "id": RuntimeValue(default_factory=lambda: str(int(time.time() * 1000))),
        "sum": {"amount": RuntimeValue(default=99), "currency": "643"},
        "paymentMethod": {"type": "Account", "accountId": "643"},
        "fields": {"account": RuntimeValue(), "order_id": RuntimeValue()},
    }

    phone_number: str = Field(..., schema_path="fields.account")
    order_id: str = Field(..., schema_path="fields.order_id")
