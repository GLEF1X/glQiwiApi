"""Main model: Partner"""
from typing import List, Optional

from pydantic import BaseModel

from glQiwiApi.utils.basics import custom_load


class Partner(BaseModel):
    """ Base partner class """
    title: str
    id: int

    maps: Optional[List[str]] = None

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()


__all__ = ("Partner",)
