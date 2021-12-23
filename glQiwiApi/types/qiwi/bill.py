from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import datetime
from typing import Any, Dict, Optional, Union

from pydantic import Extra, Field

from glQiwiApi.types.amount import HashableOptionalSum, PlainAmount
from glQiwiApi.types.base import Base, HashableBase
from glQiwiApi.types.exceptions import WebhookSignatureUnverifiedError


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

    amount: HashableOptionalSum
    status: BillStatus
    site_id: str = Field(..., alias="siteId")
    bill_id: str = Field(..., alias="billId")
    pay_url: str = Field(..., alias="payUrl")
    creation_date_time: datetime = Field(..., alias="creationDateTime")
    expiration_date_time: datetime = Field(..., alias="expirationDateTime")
    custom_fields: CustomFields = Field(None, alias="customFields")
    customer: Optional[Customer] = None

    @property
    def invoice_uid(self) -> str:
        return self.pay_url[-36:]

    class Config:
        extra = Extra.allow
        allow_mutation = True

    async def check(self) -> bool:
        return (await self.client.check_p2p_bill_status(bill_id=self.bill_id)) == "PAID"

    async def reject(self) -> Bill:
        return await self.client.reject_p2p_bill(bill_id=self.bill_id)


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


class BillWebhook(HashableBase):
    """Object: BillWebhook"""

    version: str = Field(..., alias="version")
    bill: Bill = Field(..., alias="bill")

    def __repr__(self) -> str:
        return f"#{self.bill.bill_id} {self.bill.amount} {self.bill.status} "

    def verify_signature(self, sha256_signature: str, secret_p2p_key: str) -> None:
        webhook_key = base64.b64decode(bytes(secret_p2p_key, "utf-8"))
        bill = self.bill

        invoice_params = f"{bill.amount.currency}|{bill.amount.value}|{bill.bill_id}|{bill.site_id}|{bill.status.value}"
        generated_signature = hmac.new(
            webhook_key, invoice_params.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        if generated_signature != sha256_signature:
            raise WebhookSignatureUnverifiedError()


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
    "BillWebhook",
    "P2PKeys",
    "InvoiceStatus",
    "BillStatus",
)
