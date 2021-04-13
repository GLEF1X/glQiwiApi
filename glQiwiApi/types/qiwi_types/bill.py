from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field

from glQiwiApi.mixins import BillMixin
from glQiwiApi.types.basics import OptionalSum
from glQiwiApi.utils.basics import custom_load


class Customer(BaseModel):
    phone: str
    email: str
    account: str


class BillStatus(BaseModel):
    value: str
    changed_datetime: datetime = Field(alias="changedDateTime")


class CustomFields(BaseModel):
    pay_sources_filter: str = Field(alias="paySourcesFilter")
    theme_code: str = Field(alias="themeCode")


class BillError(BaseModel):
    service_name: str = Field(alias="serviceName")
    error_code: str = Field(alias="errorCode")
    description: str
    user_message: str = Field(alias="userMessage")
    datetime: str = Field(alias="dateTime")
    trace_id: str = Field(alias="traceId")

    class Config:
        json_loads = custom_load


class Bill(BaseModel, BillMixin):
    site_id: str = Field(alias="siteId")
    bill_id: str = Field(alias="billId")
    amount: OptionalSum
    status: BillStatus
    creation_date_time: datetime = Field(alias="creationDateTime")
    expiration_date_time: datetime = Field(alias="expirationDateTime")
    pay_url: str = Field(alias="payUrl")
    custom_fields: Optional[
        CustomFields
    ] = Field(alias="customFields", const=None)
    customer: Optional[Customer] = None

    class Config:
        extra = 'allow'
        json_loads = custom_load
        allow_mutation = True


class RefundBill(BaseModel):
    """
    Модель счёта киви апи

    """
    amount: OptionalSum
    datetime: datetime
    refund_id: str = Field(..., alias="refundId")
    status: str

    def as_str(self) -> str:
        return f"№{self.refund_id} {self.status} {self.amount} {self.datetime}"

    def get_value(self) -> Union[float, int]:
        return self.amount.value


__all__ = [
    'Bill', 'BillError', 'RefundBill'
]
