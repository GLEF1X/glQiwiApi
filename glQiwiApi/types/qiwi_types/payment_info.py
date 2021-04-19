from typing import Optional

from pydantic import BaseModel, Field

from glQiwiApi.types import Sum


class Fields(BaseModel):
    account: str


class State(BaseModel):
    code: str


class TransactionInfo(BaseModel):
    txn_id: int = Field(..., alias="id")
    state: State


class PaymentInfo(BaseModel):
    payment_id: int = Field(..., alias="id")
    terms: str
    fields: Fields
    payment_sum: Sum = Field(..., alias="sum")
    source: str
    transaction: Optional[TransactionInfo] = None
    comment: Optional[str] = None


__all__ = [
    'PaymentInfo'
]
