from typing import Optional, Dict, Any

from pydantic import Field, validator

from glQiwiApi.base.types.amount import AmountWithCurrency, CurrencyModel
from glQiwiApi.base.types.base import HashableBase
from glQiwiApi.utils.currency_util import Currency


class Balance(HashableBase):
    """object: Balance"""

    alias: str
    title: str
    fs_alias: str = Field(alias="fsAlias")
    bank_alias: str = Field(alias="bankAlias")
    has_balance: bool = Field(alias="hasBalance")
    balance: Optional[AmountWithCurrency] = None
    currency: CurrencyModel
    account_type: Optional[Dict[str, Any]] = Field(None, alias="type")
    is_default_account: bool = Field(alias="defaultAccount")

    @validator("currency", pre=True)
    def humanize_pay_currency(cls, v):  # type: ignore
        if not isinstance(v, int):
            return v
        return Currency.get(str(v))


__all__ = "Account"
