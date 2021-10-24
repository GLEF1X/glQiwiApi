from typing import List

from pydantic import Field

from glQiwiApi.types.base import ExtraBase
from glQiwiApi.types.amount import CurrencyAmount


class Statistic(ExtraBase):
    """object: Statistic"""

    incoming: List[CurrencyAmount] = Field(alias="incomingTotal")
    out: List[CurrencyAmount] = Field(alias="outgoingTotal")


__all__ = ["Statistic"]
