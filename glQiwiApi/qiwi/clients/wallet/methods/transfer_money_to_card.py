import time
from typing import ClassVar, Dict, Any, Union

from pydantic import Field

from glQiwiApi.base.api_method import RuntimeValue
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import PaymentInfo


class TransferMoneyToCard(QiwiAPIMethod[PaymentInfo]):
    http_method: ClassVar[str] = "POST"
    url: ClassVar[str] = "https://edge.qiwi.com/sinap/api/v2/terms/{private_card_id}"

    request_schema: ClassVar[Dict[str, Any]] = {
        "id": RuntimeValue(default_factory=lambda: str(int(time.time() * 1000))),
        "sum": {
            "amount": RuntimeValue(),
            "currency": "643"
        },
        "paymentMethod": {
            "type": "Account",
            "accountId": "643"
        },
        "fields": {
            "account": RuntimeValue()
        },
    }

    private_card_id: str = Field(..., path_runtime_value=True)
    amount: Union[int, float]
    card_number: str
