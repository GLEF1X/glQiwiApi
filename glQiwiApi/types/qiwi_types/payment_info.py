from typing import Optional

from pydantic import Field

from glQiwiApi.types import Sum
from glQiwiApi.types.base import Base


class Fields(Base):
    """ Специальные поля """

    account: str


class State(Base):
    """ State """

    code: str


class TransactionInfo(Base):
    """ Информация о транзакции """

    txn_id: int = Field(..., alias="id")
    state: State


class PaymentInfo(Base):
    """Информация о платеже"""

    payment_id: int = Field(..., alias="id")
    terms: str
    fields: Optional[Fields] = None
    payment_sum: Sum = Field(..., alias="sum")
    source: str
    transaction: Optional[TransactionInfo] = None
    comment: Optional[str] = None


__all__ = ["PaymentInfo"]
