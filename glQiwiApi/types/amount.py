from typing import Optional, Union

from pydantic import BaseConfig, BaseModel, Field, validator

from glQiwiApi.types.base import Base, HashableBase


class CurrencyModel(HashableBase):
    code: str
    decimal_digits: int
    name: str
    name_plural: str
    rounding: Union[int, float]
    symbol: str
    symbol_native: str
    iso_format: Optional[str] = Field(..., alias='isoformat')

    def __str__(self) -> str:
        return self.code

    class Config(BaseConfig):
        frozen = True
        allow_mutation = False


class AmountWithCurrency(Base):
    amount: float
    currency: Union[CurrencyModel, str]  # string if currency util couldn't parse it

    @validator('currency', pre=True)
    def humanize_pay_currency(cls, v):  # type: ignore
        from glQiwiApi.utils.currency_util import Currency

        if not isinstance(v, int):
            try:
                v = int(v)
            except ValueError:
                return v
        return Currency.get(str(v))


class HashableSum(HashableBase, AmountWithCurrency):
    ...


class PlainAmount(BaseModel):
    value: float
    currency: str


class HashablePlainAmount(HashableBase, PlainAmount):
    ...


class Type(BaseModel):
    id: str
    title: str
