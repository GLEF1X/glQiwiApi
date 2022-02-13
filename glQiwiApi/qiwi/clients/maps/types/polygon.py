from pydantic import Field, BaseModel


class Polygon(BaseModel):
    """Polygon class for QiwiMaps class"""

    latitude_north_western: float = Field(..., alias="latNW")
    longitude_north_western: float = Field(..., alias="lngNW")
    latitude_south_east: float = Field(..., alias="latSE")
    longitude_south_east: float = Field(..., alias="lngSE")
