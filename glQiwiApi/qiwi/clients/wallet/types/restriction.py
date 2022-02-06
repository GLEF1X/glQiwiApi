from pydantic import Field

from glQiwiApi.types.base import HashableBase


class Restriction(HashableBase):
    code: str = Field(..., alias="restrictionCode")
    description: str = Field(..., alias="restrictionDescription")


__all__ = ("Restriction",)
