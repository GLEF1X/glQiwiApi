from typing import List

from pydantic import BaseModel, Field

from glQiwiApi.data_models.basics import Sum
from glQiwiApi.utils import custom_load


class Statistic(BaseModel):
    incoming: List[Sum] = Field(alias="incomingTotal")
    out: List[Sum] = Field(alias="outgoingTotal")

    class Config:
        json_loads = custom_load


__all__ = [
    'Statistic'
]
