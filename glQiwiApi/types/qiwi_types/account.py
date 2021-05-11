from typing import Optional

from pydantic import BaseModel, Field, validator

from glQiwiApi.types.basics import Sum, Type
from glQiwiApi.types.qiwi_types.currency_parsed import CurrencyModel
from glQiwiApi.utils.currency_util import Currency


class Account(BaseModel):
    """ object: Account """
    alias: str
    title: str
    fs_alias: str = Field(alias="fsAlias")
    bank_alias: str = Field(alias="bankAlias")
    has_balance: bool = Field(alias="hasBalance")
    balance: Optional[Sum] = Field(const=None)
    currency: CurrencyModel
    account_type: Optional[Type] = Field(None, alias="type")
    is_default_account: bool = Field(alias="defaultAccount")

    @validator("currency", pre=True, check_fields=True)
    def humanize_pay_currency(cls, v):
        if not isinstance(v, int):
            return v
        return Currency.get(str(v))


__all__ = (
    'Account'
)
