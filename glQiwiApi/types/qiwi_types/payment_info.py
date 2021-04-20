from typing import Optional

from pydantic import BaseModel, Field

from glQiwiApi.types import Sum
from glQiwiApi.utils.basics import custom_load


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
    fields: Fields
    payment_sum: Sum = Field(..., alias="sum")
    source: str
    transaction: Optional[TransactionInfo] = None
    comment: Optional[str] = None

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()


__all__ = [
    'PaymentInfo'
]
