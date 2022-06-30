from datetime import datetime
from typing import Union

from pydantic import Field

from glQiwiApi.types.amount import Currency
from glQiwiApi.types.base import Base


class Interval(Base):
    """object: Interval"""

    date_from: datetime = Field(alias='dateFrom')
    date_till: datetime = Field(alias='dateTill')


class Limit(Base):
    """object: Limit"""

    currency: Currency
    rest: Union[float, int]
    max_limit: Union[float, int] = Field(alias='max')
    spent: Union[float, int]
    interval: Interval
    limit_type: str = Field(alias='type')


__all__ = ['Limit']
