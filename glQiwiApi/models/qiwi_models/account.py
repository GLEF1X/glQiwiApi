from typing import Optional

from pydantic import BaseModel, Field

from glQiwiApi.models.basics import Sum


class Account(BaseModel):
    alias: str
    fs_alias: str = Field(alias="fsAlias")
    bank_alias: str = Field(alias="bankAlias")
    title: str
    has_balance: bool = Field(alias="hasBalance")
    balance: Optional[Sum] = Field(const=None)
    currency: str


__all__ = [
    'Account'
]
