from datetime import datetime
from typing import Union

from pydantic import BaseModel, Field

from glQiwiApi.utils.basics import custom_load


class Interval(BaseModel):
    """ object: Interval """
    date_from: datetime = Field(alias="dateFrom")
    date_till: datetime = Field(alias="dateTill")


class Limit(BaseModel):
    """ object: Limit """
    currency: str
    rest: Union[float, int]
    max_limit: Union[float, int] = Field(alias="max")
    spent: Union[float, int]
    interval: Interval
    limit_type: str = Field(alias="type")

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()


__all__ = [
    'Limit'
]
