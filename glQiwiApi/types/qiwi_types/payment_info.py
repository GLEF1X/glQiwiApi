from typing import Optional

from pydantic import BaseModel, Field

from glQiwiApi.types import Sum


class Fields(BaseModel):
    """ Специальные поля """
    account: str


class State(BaseModel):
    """ State """
    code: str


class TransactionInfo(BaseModel):
    """ Информация о транзакции """
    txn_id: int = Field(..., alias="id")
    state: State


class PaymentInfo(BaseModel):
    """Информация о платеже"""
    payment_id: int = Field(..., alias="id")
    terms: str
    fields: Optional[Fields] = None
    payment_sum: Sum = Field(..., alias="sum")
    source: str
    transaction: Optional[TransactionInfo] = None
    comment: Optional[str] = None


__all__ = [
    'PaymentInfo'
]
