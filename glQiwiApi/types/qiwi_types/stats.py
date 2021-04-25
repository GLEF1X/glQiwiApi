from typing import List

from pydantic import BaseModel, Field

from glQiwiApi.types.basics import Sum
from glQiwiApi.utils.basics import custom_load


class Statistic(BaseModel):
    """ object: Statistic """
    incoming: List[Sum] = Field(alias="incomingTotal")
    out: List[Sum] = Field(alias="outgoingTotal")

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()


__all__ = [
    'Statistic'
]
