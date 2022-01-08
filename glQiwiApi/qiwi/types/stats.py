from typing import List

from pydantic import Field

from glQiwiApi.base_types.amount import AmountWithCurrency
from glQiwiApi.qiwi.types.base import QiwiWalletResultBaseWithClient


class Statistic(QiwiWalletResultBaseWithClient):
    """object: Statistic"""

    incoming: List[AmountWithCurrency] = Field(alias="incomingTotal")
    out: List[AmountWithCurrency] = Field(alias="outgoingTotal")


__all__ = ["Statistic"]
