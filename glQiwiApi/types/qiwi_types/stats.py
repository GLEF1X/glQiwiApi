from typing import List

from pydantic import BaseModel, Field

from glQiwiApi.types.basics import Sum


class Statistic(BaseModel):
    """ object: Statistic """
    incoming: List[Sum] = Field(alias="incomingTotal")
    out: List[Sum] = Field(alias="outgoingTotal")


__all__ = [
    'Statistic'
]
