from typing import Literal, Optional

from pydantic import BaseModel, Field

from glQiwiApi.types.basics import OptionalSum
from glQiwiApi.mixins import BillMixin
from glQiwiApi.utils.basics import custom_load


class Customer(BaseModel):
    phone: str
    email: str
    account: str


class BillStatus(BaseModel):
    value: Literal['WAITING', 'PAID', 'REJECTED', 'EXPIRED']
    changed_datetime: str = Field(alias="changedDateTime")


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
    creation_date_time: str = Field(alias="creationDateTime")
    expiration_date_time: str = Field(alias="expirationDateTime")
    pay_url: str = Field(alias="payUrl")
    custom_fields: Optional[CustomFields] = Field(alias="customFields", const=None)
    customer: Optional[Customer] = None

    class Config:
        extra = 'allow'
        json_loads = custom_load
        allow_mutation = True


__all__ = [
    'Bill', 'BillError'
]
