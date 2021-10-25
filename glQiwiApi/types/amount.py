from __future__ import annotations

from typing import Union, Optional

from pydantic import BaseModel, validator, Field

from glQiwiApi.types.base import HashableBase


class CurrencyModel(HashableBase):
    code: str
    decimal_digits: int
    name: str
    name_plural: str
    rounding: Union[int, float]
    symbol: str
    symbol_native: str
    iso_format: Optional[str] = Field(..., alias="isoformat")


class CurrencyAmount(BaseModel):
    amount: float
    currency: Union[CurrencyModel, str]  # string if currency util couldn't parse it

    @validator("currency", pre=True)
    def humanize_pay_currency(cls, v):  # type: ignore
        from glQiwiApi.utils.currency_util import Currency

        if not isinstance(v, int):
            try:
                v = int(v)
            except ValueError:
                return v
        return Currency.get(str(v))


class HashableSum(HashableBase, CurrencyAmount):
    ...


class PlainAmount(BaseModel):
    value: float
    currency: str


class HashableOptionalSum(HashableBase, PlainAmount):
    ...


class Type(BaseModel):
    id: str
    title: str
