from typing import List

from pydantic import BaseModel, Field

from glQiwiApi.models.basics import Sum


class Statistic(BaseModel):
    incoming: List[Sum] = Field(alias="incomingTotal")
    out: List[Sum] = Field(alias="outgoingTotal")


__all__ = [
    'Statistic'
]
