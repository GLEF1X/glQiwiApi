import datetime
from typing import Optional, List

from pydantic import Field

from glQiwiApi.types import CurrencyAmount
from glQiwiApi.types.base import Base


class OrderDetails(Base):
    """object: OrderDetails"""

    order_id: str = Field(..., alias="id")
    card_alias: str = Field(..., alias="cardAlias")
    status: str
    price: Optional[CurrencyAmount] = None
    card_id: Optional[str] = Field(alias="cardId", default=None)


class CardCredentials(Base):
    """object: CardCredentials"""

    qvx_id: int = Field(..., alias="id")
    masked_pan: str = Field(..., alias="maskedPan")
    status: str
    card_expire: datetime.datetime = Field(..., alias="cardExpire")
    card_type: str = Field(..., alias="cardType")
    card_alias: Optional[str] = Field(..., alias="cardAlias")
    activated: datetime.datetime
    sms_recender: Optional[datetime.datetime] = Field(..., alias="smsResended")
    post_number: Optional[str] = Field(default=None, alias="postNumber")
    blocked_date: Optional[datetime.datetime] = Field(default=None, alias="blockedDate")
    card_id: int = Field(..., alias="cardId")
    txn_id: int = Field(..., alias="txnId")
    card_expire_month: str = Field(..., alias="cardExpireMonth")
    card_expire_year: str = Field(..., alias="cardExpireYear")


class Requisite(Base):
    """object: Requisite"""

    name: str
    value: str


class Details(Base):
    """object: Details"""

    info: str
    description: str
    tariff_link: str = Field(..., alias="tariffLink")
    offer_link: str = Field(..., alias="offerLink")
    features: List[str]
    requisites: List[Requisite]


class CardInfo(Base):
    """object: CardInfo"""

    id_: int = Field(..., alias="id")
    name: str
    alias: str
    price: CurrencyAmount
    period: str
    type_: str = Field(..., alias="type")
    details: Details


class Card(Base):
    """
    object: Card
    description: Данные выпущенных карт
    """

    details: CardCredentials = Field(..., alias="qvx")
    balance: Optional[CurrencyAmount] = None
    info: CardInfo


__all__ = ("OrderDetails", "Card")
