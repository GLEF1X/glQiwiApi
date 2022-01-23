from typing import Any, Dict, Optional

from pydantic import Field

from glQiwiApi.base.types.amount import AmountWithCurrency
from glQiwiApi.base.types.base import Base


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
    payment_sum: AmountWithCurrency = Field(..., alias="sum")
    terms: str
    fields: Fields
    source: str
    transaction: Optional[TransactionInfo] = None
    comment: Optional[str] = None


class PaymentMethod(Base):
    type: str = "Account"
    account_id: int = Field(643, alias="accountId")


class QiwiPayment(Base):
    id: int
    sum: AmountWithCurrency
    method: PaymentMethod = Field(..., alias="paymentMethod")
    fields: Dict[Any, Any]
    comment: Optional[str] = None


__all__ = ["PaymentInfo", "QiwiPayment"]
