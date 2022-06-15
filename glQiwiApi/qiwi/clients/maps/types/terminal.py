from typing import Optional

from pydantic import Field

from glQiwiApi.types.base import Base


class Coordinate(Base):
    """Object: coordinate"""

    latitude: float = Field(..., alias='latitude')
    longitude: float = Field(..., alias='longitude')
    precision: int = Field(..., alias='precision')


class Terminal(Base):
    """Object: Terminal"""

    terminal_id: int = Field(..., alias='terminalId')
    ttp_id: int = Field(..., alias='ttpId')
    last_active: str = Field(..., alias='lastActive')
    count: int = Field(..., alias='count')
    address: str = Field(..., alias='address')
    verified: bool = Field(..., alias='verified')
    label: str = Field(..., alias='label')
    description: Optional[str] = Field(type(None), alias='description')
    cash_allowed: bool = Field(..., alias='cashAllowed')
    card_allowed: bool = Field(..., alias='cardAllowed')
    identification_type: int = Field(..., alias='identificationType')
    coordinate: Coordinate = Field(..., alias='coordinate')
