"""Main model: Terminal"""
from typing import Optional

from pydantic import Field, BaseModel

from glQiwiApi.utils.basics import custom_load


class Coordinate(BaseModel):
    """Object: coordinate"""

    latitude: float = Field(..., alias="latitude")
    longitude: float = Field(..., alias="longitude")
    precision: int = Field(..., alias="precision")


class Terminal(BaseModel):
    """Object: Terminal"""

    terminal_id: int = Field(..., alias="terminalId")
    ttp_id: int = Field(..., alias="ttpId")
    last_active: str = Field(..., alias="lastActive")
    count: int = Field(..., alias="count")
    address: str = Field(..., alias="address")
    verified: bool = Field(..., alias="verified")
    label: str = Field(..., alias="label")
    description: Optional[str] = Field(type(None), alias="description")
    cash_allowed: bool = Field(..., alias="cashAllowed")
    card_allowed: bool = Field(..., alias="cardAllowed")
    identification_type: int = Field(..., alias="identificationType")
    coordinate: Coordinate = Field(..., alias="coordinate")

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()


__all__ = ("Terminal",)
