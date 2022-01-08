from typing import Any, Dict, Optional

from pydantic import Field

from glQiwiApi.base_types import AmountWithCurrency
from glQiwiApi.qiwi.types.base import QiwiWalletResultBaseWithClient


class Fields(QiwiWalletResultBaseWithClient):
    """object: Fields"""

    account: str


class State(QiwiWalletResultBaseWithClient):
    """object: State"""

    code: str


class TransactionInfo(QiwiWalletResultBaseWithClient):
    """object: TransactionInfo"""

    txn_id: int = Field(..., alias="id")
    state: State


class PaymentInfo(QiwiWalletResultBaseWithClient):
    """object: PaymentInfo"""

    payment_id: int = Field(..., alias="id")
    terms: str
    fields: Optional[Fields] = None
    payment_sum: AmountWithCurrency = Field(..., alias="sum")
    source: str
    transaction: Optional[TransactionInfo] = None
    comment: Optional[str] = None


class PaymentMethod(QiwiWalletResultBaseWithClient):
    type: str = "Account"
    account_id: int = Field(643, alias="accountId")


class QiwiPayment(QiwiWalletResultBaseWithClient):
    id: int
    sum: AmountWithCurrency
    method: PaymentMethod = Field(..., alias="paymentMethod")
    fields: Dict[Any, Any]
    comment: Optional[str] = None


__all__ = ["PaymentInfo", "QiwiPayment"]
