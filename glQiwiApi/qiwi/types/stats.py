from typing import List

from pydantic import Field

from glQiwiApi.base_types.amount import AmountWithCurrency
from glQiwiApi.base_types.base import ExtraBase


class Statistic(ExtraBase):
    """object: Statistic"""

    incoming: List[AmountWithCurrency] = Field(alias="incomingTotal")
    out: List[AmountWithCurrency] = Field(alias="outgoingTotal")


__all__ = ["Statistic"]
