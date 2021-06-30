from pydantic import Field

from glQiwiApi.types.base import Base


class Restriction(Base):
    code: str = Field(..., alias="restrictionCode")
    description: str = Field(..., alias="restrictionDescription")


__all__ = ("Restriction",)
