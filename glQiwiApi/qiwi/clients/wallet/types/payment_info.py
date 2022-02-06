from typing import Any, Dict, Optional

from pydantic import Field

from glQiwiApi.types.amount import AmountWithCurrency
from glQiwiApi.types.base import Base


class Fields(Base):
    """object: Fields"""

    account: str


class State(Base):
    """object: State"""

    code: str


class TransactionInfo(Base):
    """object: TransactionInfo"""

    id: int
    state: State


class PaymentInfo(Base):
    """object: PaymentInfo"""

    id: int
    amount: AmountWithCurrency = Field(..., alias="sum")
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
