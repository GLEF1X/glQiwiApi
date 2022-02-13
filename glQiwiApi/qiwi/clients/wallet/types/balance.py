from typing import Optional, Dict, Any, Union

from pydantic import Field, validator

from glQiwiApi.types.amount import CurrencyModel, AmountWithCurrency
from glQiwiApi.types.base import HashableBase
from glQiwiApi.utils.currency_util import Currency


class AvailableBalance(HashableBase):
    alias: str
    currency: Union[str, CurrencyModel]


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
