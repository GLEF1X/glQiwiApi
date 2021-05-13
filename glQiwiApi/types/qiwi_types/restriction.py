from pydantic import BaseModel, Field


class Restriction(BaseModel):
    code: str = Field(..., alias="restrictionCode")
    description: str = Field(..., alias="restrictionDescription")


__all__ = ('Restriction',)
