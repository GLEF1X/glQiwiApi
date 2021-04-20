"""Main model: Partner"""
from typing import List, Optional

from pydantic import BaseModel

from glQiwiApi.utils.basics import custom_load


class Partner(BaseModel):
    title: str
    id: int

    maps: Optional[List[str]] = None

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return super().__str__()

        def __repr__(self) -> str:
            return super().__repr__()


__all__ = ("Partner",)
