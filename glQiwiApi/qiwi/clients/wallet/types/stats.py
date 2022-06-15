from typing import List

from pydantic import Field

from glQiwiApi.types.amount import AmountWithCurrency
from glQiwiApi.types.base import Base


class Statistic(Base):
    """object: Statistic"""

    incoming: List[AmountWithCurrency] = Field(alias='incomingTotal')
    out: List[AmountWithCurrency] = Field(alias='outgoingTotal')


__all__ = ['Statistic']
