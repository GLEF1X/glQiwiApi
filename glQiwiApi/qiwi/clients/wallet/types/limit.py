from datetime import datetime
from typing import Union

from pydantic import Field, validator

from glQiwiApi.types.amount import CurrencyModel
from glQiwiApi.types.base import Base
from glQiwiApi.utils.currency_util import Currency


class Interval(Base):
    """object: Interval"""

    date_from: datetime = Field(alias='dateFrom')
    date_till: datetime = Field(alias='dateTill')


class Limit(Base):
    """object: Limit"""

    currency: CurrencyModel
    rest: Union[float, int]
    max_limit: Union[float, int] = Field(alias='max')
    spent: Union[float, int]
    interval: Interval
    limit_type: str = Field(alias='type')

    @validator('currency', pre=True)
    def currency_validate(cls, v):  # type: ignore
        if not isinstance(v, str):
            raise ValueError()
        return Currency.get(v)


__all__ = ['Limit']
