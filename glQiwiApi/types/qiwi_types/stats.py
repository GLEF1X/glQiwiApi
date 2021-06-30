from typing import List

from pydantic import Field

from glQiwiApi.types.base import Base
from glQiwiApi.types.basics import Sum


class Statistic(Base):
    """ object: Statistic """

    incoming: List[Sum] = Field(alias="incomingTotal")
    out: List[Sum] = Field(alias="outgoingTotal")


__all__ = ["Statistic"]
