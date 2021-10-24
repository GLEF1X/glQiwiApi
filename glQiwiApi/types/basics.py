from __future__ import annotations

from typing import Union, Any

from pydantic import BaseModel, validator

from glQiwiApi.types.base import HashableBase


class CurrencyAmount(BaseModel):
    """
    Сумма платежа

    """

    amount: Union[int, float, str]
    currency: Any

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


class OptionalSum(BaseModel):
    """object: OptionalSum"""

    value: Union[int, float]
    currency: str


class HashableOptionalSum(HashableBase, OptionalSum):
    ...


class Type(BaseModel):
    """
    Базовая модель типа данных

    """

    id: str
    title: str


__all__ = ("CurrencyAmount", "OptionalSum", "Type", "HashableOptionalSum", "HashableSum")
