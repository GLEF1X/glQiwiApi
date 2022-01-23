import uuid
from datetime import datetime, timedelta
from typing import ClassVar, Dict, Any, Optional, Union, List

from pydantic import Field

from glQiwiApi.base.api_method import APIMethod, RuntimeValue
from glQiwiApi.qiwi.clients.p2p.types import Bill


def get_default_bill_time() -> datetime:
    return datetime.now() + timedelta(days=2)


class CreateP2PBill(APIMethod[Bill]):
    http_method: ClassVar[str] = "PUT"
    url: ClassVar[str] = "https://api.qiwi.com/partner/bill/v1/bills/{bill_id}"

    request_schema: ClassVar[Dict[str, Any]] = {
        "amount": {
            "currency": "RUB",
            "value": RuntimeValue()
        },
        "expirationDateTime": RuntimeValue(),
        "comment": RuntimeValue(),
        "customFields": {
            "paySourcesFilter": RuntimeValue(default="qw"),
            "themeCode": RuntimeValue(default="Yvan-YKaSh"),
        },
    }

    bill_id: str = Field(default_factory=lambda: str(uuid.uuid4()), path_runtime_value=True)
    expire_at: datetime = Field(default_factory=get_default_bill_time, scheme_path="expirationDateTime")
    amount: Union[int, float, str] = Field(..., scheme_path="amount.value")
    comment: Optional[str] = Field(None, scheme_path="comment")
    theme_code: Optional[str] = Field(None, scheme_path="customFields.themeCode")
    pay_source_filter: Optional[List[str]] = Field(None, scheme_path="customFields.paySourcesFilter")
