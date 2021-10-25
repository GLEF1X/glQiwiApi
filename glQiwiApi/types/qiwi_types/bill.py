import base64
import hashlib
import hmac
import warnings
from datetime import datetime
from typing import Optional, Union, Dict, Any

from pydantic import Field, Extra

from glQiwiApi.types.amount import PlainAmount, HashableOptionalSum
from glQiwiApi.types.base import Base, HashableBase
from glQiwiApi.types.exceptions import WebhookSignatureUnverified


class Customer(HashableBase):
    """Object: Customer"""

    phone: Optional[str] = None
    email: Optional[str] = None
    account: Optional[str] = None


class BillStatus(HashableBase):
    """Object: BillStatus"""

    value: str
    changed_datetime: Optional[datetime] = Field(None, alias="changedDateTime")


class CustomFields(HashableBase):
    """Object: CustomFields"""

    pay_sources_filter: Optional[str] = Field(None, alias="paySourcesFilter")
    theme_code: Optional[str] = Field(None, alias="themeCode")


class BillError(HashableBase):
    """Object: BillError"""

    service_name: str = Field(..., alias="serviceName")
    error_code: str = Field(..., alias="errorCode")
    description: str
    user_message: str = Field(..., alias="userMessage")
    datetime: str = Field(..., alias="dateTime")
    trace_id: str = Field(..., alias="traceId")


class Bill(HashableBase):
    """Object: Bill"""

    site_id: str = Field(..., alias="siteId")
    bill_id: str = Field(..., alias="billId")
    amount: HashableOptionalSum
    status: BillStatus
    creation_date_time: Optional[datetime] = Field(None, alias="creationDateTime")
    expiration_date_time: Optional[datetime] = Field(None, alias="expirationDateTime")
    pay_url: Optional[str] = Field(None, alias="payUrl")
    custom_fields: Optional[CustomFields] = Field(None, alias="customFields")
    customer: Optional[Customer] = None
    workaround_url: Optional[str] = None

    class Config:
        extra = Extra.allow
        allow_mutation = True

    @property
    async def paid(self) -> bool:
        warnings.warn(
            "`Bill.paid` property is deprecated, and will be removed in next versions, "
            "use `Bill.check(...)` instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return await self.check()

    async def check(self) -> bool:
        """Checking p2p payment status"""
        return (await self.client.check_p2p_bill_status(bill_id=self.bill_id)) == "PAID"

    async def reject(self) -> None:
        await self.client.reject_p2p_bill(bill_id=self.bill_id)


class RefundBill(Base):
    """object: RefundBill"""

    amount: PlainAmount
    datetime: datetime
    refund_id: str = Field(..., alias="refundId")
    status: str

    def as_str(self) -> str:
        return f"№{self.refund_id} {self.status} {self.amount} {self.datetime}"

    def get_value(self) -> Union[float, int]:
        return self.amount.value


class Notification(HashableBase):
    """Object: Notification"""

    version: str = Field(..., alias="version")
    bill: Bill = Field(..., alias="bill")

    def __repr__(self) -> str:
        return f"#{self.bill.bill_id} {self.bill.amount} {self.bill.status} "

    def verify_signature(self, sha256_signature: str, webhook_base64_key: str) -> None:
        webhook_key = base64.b64decode(bytes(webhook_base64_key, "utf-8"))
        bill = self.bill

        invoice_params = f"{bill.amount.currency}|{bill.amount.value}|{bill.bill_id}|{bill.site_id}|{bill.status.value}"
        generated_signature = hmac.new(
            webhook_key, invoice_params.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        if generated_signature != sha256_signature:
            raise WebhookSignatureUnverified()


class P2PKeys(Base):
    public_key: str = Field(..., alias="PublicKey")
    secret_key: str = Field(..., alias="SecretKey")


class InvoiceStatus(Base):
    invoice_status: str
    is_sms_confirm: bool
    pay_results: Dict[Any, Any] = Field(..., alias="WALLET_ACCEPT_PAY_RESULT")


__all__ = (
    "Bill",
    "BillError",
    "RefundBill",
    "Notification",
    "P2PKeys",
    "InvoiceStatus",
    "BillStatus",
)
