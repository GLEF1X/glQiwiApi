from typing import Optional

from pydantic import BaseModel, Field

from glQiwiApi.utils.basics import custom_load


class Identification(BaseModel):
    identification_id: int = Field(..., alias="id")
    first_name: str = Field(..., alias="firstName")
    middle_name: str = Field(..., alias="middleName")
    last_name: str = Field(..., alias="lastName")
    birth_date: str = Field(..., alias="birthDate")
    passport: str
    inn: Optional[str]
    snils: Optional[str]
    oms: Optional[str]
    type: str

    class Config:
        json_loads = custom_load
