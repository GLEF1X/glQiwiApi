from typing import Optional

from pydantic import BaseModel, Field

from glQiwiApi.data_models.basics import Sum, Type
from glQiwiApi.utils import custom_load


class Account(BaseModel):
    alias: str
    fs_alias: str = Field(alias="fsAlias")
    bank_alias: str = Field(alias="bankAlias")
    title: str
    has_balance: bool = Field(alias="hasBalance")
    balance: Optional[Sum] = Field(const=None)
    currency: int
    account_type: Optional[Type] = Field(None, alias="type")
    is_default_account: bool = Field(alias="defaultAccount")

    class Config:
        json_loads = custom_load


__all__ = [
    'Account'
]
