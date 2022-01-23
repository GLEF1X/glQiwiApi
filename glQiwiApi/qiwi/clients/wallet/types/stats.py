from typing import List

from pydantic import Field

from glQiwiApi.base.types.amount import AmountWithCurrency
from glQiwiApi.base.types.base import Base


class Statistic(Base):
    """object: Statistic"""

    incoming: List[AmountWithCurrency] = Field(alias="incomingTotal")
    out: List[AmountWithCurrency] = Field(alias="outgoingTotal")


__all__ = ["Statistic"]
