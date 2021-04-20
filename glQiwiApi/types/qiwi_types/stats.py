from typing import List

from pydantic import BaseModel, Field

from glQiwiApi.types.basics import Sum
from glQiwiApi.utils.basics import custom_load


class Statistic(BaseModel):
    incoming: List[Sum] = Field(alias="incomingTotal")
    out: List[Sum] = Field(alias="outgoingTotal")

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return super().__str__()

        def __repr__(self) -> str:
            return super().__repr__()


__all__ = [
    'Statistic'
]
