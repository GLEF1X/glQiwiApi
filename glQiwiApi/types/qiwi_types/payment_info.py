from typing import Optional, Any, Dict

from pydantic import Field

from glQiwiApi.types import CurrencyAmount
from glQiwiApi.types.base import Base


class Fields(Base):
    """object: Fields"""

    account: str


class State(Base):
    """object: State"""

    code: str


class TransactionInfo(Base):
    """object: TransactionInfo"""

    txn_id: int = Field(..., alias="id")
    state: State


class PaymentInfo(Base):
    """object: PaymentInfo"""

    payment_id: int = Field(..., alias="id")
    terms: str
    fields: Optional[Fields] = None
    payment_sum: CurrencyAmount = Field(..., alias="sum")
    source: str
    transaction: Optional[TransactionInfo] = None
    comment: Optional[str] = None


class PaymentMethod(Base):
    type: str = "Account"
    account_id: int = Field(643, alias="accountId")


class QiwiPayment(Base):
    id: int
    sum: CurrencyAmount
    method: PaymentMethod = Field(..., alias="paymentMethod")
    fields: Dict[Any, Any]
    comment: Optional[str] = None


__all__ = ["PaymentInfo", "QiwiPayment"]
