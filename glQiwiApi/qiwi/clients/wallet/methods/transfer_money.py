import time
from typing import ClassVar, Dict, Any

from pydantic import Field

from glQiwiApi.base.api_method import APIMethod, RuntimeValue
from glQiwiApi.qiwi.clients.wallet.types import PaymentInfo


class TransferMoney(APIMethod[PaymentInfo]):
    url: ClassVar[str] = "https://edge.qiwi.com/sinap/api/v2/terms/99/payments"
    http_method: ClassVar[str] = "POST"

    request_schema: ClassVar[Dict[str, Any]] = {
        "id": RuntimeValue(default_factory=lambda: str(int(time.time() * 1000))),
        "sum": {
            "amount": RuntimeValue(),
            "currency": "643"
        },
        "paymentMethod": {"type": "Account", "accountId": "643"},
        "comment": "",
        "fields": {
            "account": RuntimeValue()
        },
    }

    amount: int = Field(..., schema_path="sum.amount")
    comment: str
    to_wallet: str = Field(..., schema_path="fields.account")
