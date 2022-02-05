import time
from typing import ClassVar, Dict, Any, Optional

from pydantic import Field

from glQiwiApi.base.api_method import RuntimeValue
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import PaymentInfo


class TransferMoney(QiwiAPIMethod[PaymentInfo]):
    url: ClassVar[str] = "https://edge.qiwi.com/sinap/api/v2/terms/99/payments"
    http_method: ClassVar[str] = "POST"

    request_schema: ClassVar[Dict[str, Any]] = {
        "id": RuntimeValue(default_factory=lambda: str(int(time.time() * 1000))),
        "sum": {
            "amount": RuntimeValue(),
            "currency": "643"
        },
        "paymentMethod": {"type": "Account", "accountId": "643"},
        "comment": RuntimeValue(mandatory=False),
        "fields": {
            "account": RuntimeValue()
        },
    }

    amount: int = Field(..., scheme_path="sum.amount")
    to_wallet: str = Field(..., scheme_path="fields.account")
    comment: Optional[str] = Field(None, scheme_path="comment")
