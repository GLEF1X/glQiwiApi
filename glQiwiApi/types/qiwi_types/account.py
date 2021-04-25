from typing import Optional

from pydantic import BaseModel, Field

from glQiwiApi.types.basics import Sum, Type
from glQiwiApi.utils.basics import custom_load


class Account(BaseModel):
    """ object: Account """
    alias: str
    title: str
    fs_alias: str = Field(alias="fsAlias")
    bank_alias: str = Field(alias="bankAlias")
    has_balance: bool = Field(alias="hasBalance")
    balance: Optional[Sum] = Field(const=None)
    currency: int
    account_type: Optional[Type] = Field(None, alias="type")
    is_default_account: bool = Field(alias="defaultAccount")

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()


__all__ = [
    'Account'
]
