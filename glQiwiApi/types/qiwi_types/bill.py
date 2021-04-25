from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field, Extra

from glQiwiApi.core.mixins import BillMixin
from glQiwiApi.types.basics import OptionalSum
from glQiwiApi.utils.basics import custom_load


class Customer(BaseModel):
    """ Object: Customer """
    phone: Optional[str] = None
    email: Optional[str] = None
    account: Optional[str] = None


class BillStatus(BaseModel):
    """ Object: BillStatus """
    value: str
    changed_datetime: datetime = Field(alias="changedDateTime")


class CustomFields(BaseModel):
    """ Object: CustomFields """
    pay_sources_filter: Optional[str] = Field(alias="paySourcesFilter",
                                              default=None)
    theme_code: Optional[str] = Field(alias="themeCode", default=None)


class BillError(BaseModel):
    """ Object: BillError """
    service_name: str = Field(alias="serviceName")
    error_code: str = Field(alias="errorCode")
    description: str
    user_message: str = Field(alias="userMessage")
    datetime: str = Field(alias="dateTime")
    trace_id: str = Field(alias="traceId")

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()


class Bill(BaseModel, BillMixin):
    """ Object: Bill """
    site_id: str = Field(alias="siteId")
    bill_id: str = Field(alias="billId")
    amount: OptionalSum
    status: BillStatus
    creation_date_time: datetime = Field(alias="creationDateTime")
    expiration_date_time: datetime = Field(alias="expirationDateTime")
    pay_url: Optional[str] = Field(alias="payUrl", default=None)
    custom_fields: Optional[
        CustomFields
    ] = Field(alias="customFields", default=None)
    customer: Optional[Customer] = None

    class Config:
        """ Pydantic config """
        json_loads = custom_load
        extra = Extra.allow

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()


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


class Notification(BaseModel):
    """Object: Notification"""

    version: str = Field(..., alias="version")
    bill: Bill = Field(..., alias="bill")

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()

    def __str__(self) -> str:
        return f"#{self.bill.bill_id} {self.bill.amount} {self.bill.status} "

    def __repr__(self) -> str:
        return self.__str__()


__all__ = (
    'Bill',
    'BillError',
    'RefundBill',
    'Notification'
)
