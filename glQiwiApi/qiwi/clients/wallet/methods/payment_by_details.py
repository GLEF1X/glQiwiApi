import uuid
from typing import ClassVar, Dict, Any, Optional

from pydantic import Field

from glQiwiApi.core.abc.api_method import RuntimeValue
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import PaymentInfo, PaymentMethod, PaymentDetails
from glQiwiApi.types.amount import AmountWithCurrency


class MakePaymentByDetails(QiwiAPIMethod[PaymentInfo]):
    url: ClassVar[str] = "https://edge.qiwi.com/sinap/api/v2/terms/1717/payments"
    http_method: ClassVar[str] = "POST"

    json_payload_schema: ClassVar[Dict[str, Any]] = {
        "id": RuntimeValue(default_factory=lambda: str(uuid.uuid4())),
        "sum": RuntimeValue(),
        "paymentMethod": RuntimeValue(),
        "fields": RuntimeValue(),
    }

    payment_sum: AmountWithCurrency = Field(..., scheme_path="sum")
    payment_method: PaymentMethod = Field(..., scheme_path="paymentMethod")
    details: PaymentDetails = Field(..., scheme_path="fields")
    payment_id: Optional[str] = Field(None, scheme_path="id")
