from datetime import datetime
from typing import Union

from pydantic import BaseModel, Field, validator

from glQiwiApi.types.qiwi_types.currency_parsed import CurrencyModel
from glQiwiApi.utils.currency_util import Currency


class Interval(BaseModel):
    """ object: Interval """
    date_from: datetime = Field(alias="dateFrom")
    date_till: datetime = Field(alias="dateTill")


class Limit(BaseModel):
    """ object: Limit """
    currency: CurrencyModel
    rest: Union[float, int]
    max_limit: Union[float, int] = Field(alias="max")
    spent: Union[float, int]
    interval: Interval
    limit_type: str = Field(alias="type")

    @validator("currency", pre=True)
    def currency_validate(cls, v):
        if not isinstance(v, str):
            raise ValueError()
        return Currency.get(v)


__all__ = [
    'Limit'
]
