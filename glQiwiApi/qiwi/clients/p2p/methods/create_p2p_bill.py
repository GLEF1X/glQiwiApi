import uuid
from datetime import datetime, timedelta
from typing import ClassVar, Dict, Any, Optional, Union, List

from pydantic import Field

from glQiwiApi.core.abc.api_method import RuntimeValue, Request
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.p2p.types import Bill, Customer
from glQiwiApi.utils.date_conversion import datetime_to_iso8601_with_moscow_timezone


class CreateP2PBill(QiwiAPIMethod[Bill]):
    http_method: ClassVar[str] = "PUT"
    url: ClassVar[str] = "https://api.qiwi.com/partner/bill/v1/bills/{bill_id}"

    json_payload_schema: ClassVar[Dict[str, Any]] = {
        "amount": {"currency": "RUB", "value": RuntimeValue()},
        "expirationDateTime": RuntimeValue(),
        "comment": RuntimeValue(mandatory=False),
        "customFields": {
            "paySourcesFilter": RuntimeValue(default="qw"),
            "themeCode": RuntimeValue(default="Yvan-YKaSh"),
        },
        "customer": RuntimeValue(mandatory=False),
    }

    bill_id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()), path_runtime_value=True
    )
    expire_at: Optional[datetime] = Field(
        default_factory=lambda: datetime_to_iso8601_with_moscow_timezone(
            datetime.now() + timedelta(days=2)
        ),
        scheme_path="expirationDateTime",
    )
    amount: Union[int, float, str] = Field(..., scheme_path="amount.value")
    comment: Optional[str] = Field(None, scheme_path="comment")
    theme_code: Optional[str] = Field(None, scheme_path="customFields.themeCode")
    pay_source_filter: Optional[List[str]] = Field(
        None, scheme_path="customFields.paySourcesFilter"
    )
    customer: Optional[Customer] = Field(None, schema_path="customer")

    def build_request(self, **url_format_kw: Any) -> "Request":
        request = super().build_request(**url_format_kw)
        expire_at = request.json_payload.get("expirationDateTime")  # type: ignore

        if expire_at is None:
            return request

        request.json_payload["expirationDateTime"] = datetime_to_iso8601_with_moscow_timezone(expire_at)  # type: ignore
        return request
