import time
from typing import ClassVar, Any, Dict

from pydantic import Field

from glQiwiApi.base.api_method import RuntimeValue
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types.payment_info import PaymentInfo


class BuyQIWIMaster(QiwiAPIMethod[PaymentInfo]):
    url: ClassVar[str] = "https://edge.qiwi.com/person-profile/v1/persons/{phone_number}/status/restrictions"
    http_method: ClassVar[str] = "POST"

    request_schema: ClassVar[Dict[str, Any]] = {
        "id": RuntimeValue(default_factory=lambda: str(int(time.time() * 1000))),
        "sum": {
            "amount": RuntimeValue(default=2999),
            "currency": "643"
        },
        "paymentMethod": {
            "type": "Account",
            "accountId": "643"
        },
        "comment": "test",
        "fields": {
            "account": RuntimeValue(),
            "vas_alias": "qvc-master"
        },
    }

    phone_number: str = Field(..., scheme_path="fields.account")
