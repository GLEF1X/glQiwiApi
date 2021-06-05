from datetime import datetime
from typing import Optional, Union

from pydantic import Field, Extra

from glQiwiApi.types.base import Base
from glQiwiApi.types.basics import OptionalSum


class Customer(Base):
    """ Object: Customer """
    phone: Optional[str] = None
    email: Optional[str] = None
    account: Optional[str] = None


class BillStatus(Base):
    """ Object: BillStatus """
    value: str
    changed_datetime: datetime = Field(alias="changedDateTime")


class CustomFields(Base):
    """ Object: CustomFields """
    pay_sources_filter: Optional[str] = Field(alias="paySourcesFilter",
                                              default=None)
    theme_code: Optional[str] = Field(alias="themeCode", default=None)


class BillError(Base):
    """ Object: BillError """
    service_name: str = Field(alias="serviceName")
    error_code: str = Field(alias="errorCode")
    description: str
    user_message: str = Field(alias="userMessage")
    datetime: str = Field(alias="dateTime")
    trace_id: str = Field(alias="traceId")


class Bill(Base):
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
        extra = Extra.allow

        def __str__(self) -> str:
            return "<Config pydantic model {Bill}>"

        def __repr__(self) -> str:
            return self.__str__()

    @property
    async def paid(self) -> bool:
        """
        Checking p2p payment

        """
        return (await self.client.check_p2p_bill_status(
            bill_id=self.bill_id
        )) == 'PAID'


class RefundBill(Base):
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


class Notification(Base):
    """Object: Notification"""

    version: str = Field(..., alias="version")
    bill: Bill = Field(..., alias="bill")

    def __str__(self) -> str:
        return f"#{self.bill.bill_id} {self.bill.amount} {self.bill.status} "

    def __repr__(self) -> str:
        return self.__str__()


class P2PKeys(Base):
    public_key: str = Field(..., alias="PublicKey")
    secret_key: str = Field(..., alias="SecretKey")


__all__ = (
    'Bill',
    'BillError',
    'RefundBill',
    'Notification',
    'P2PKeys'
)
