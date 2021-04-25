from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from glQiwiApi.utils.basics import custom_load


class Identification(BaseModel):
    """ object: Identification """
    identification_id: int = Field(..., alias="id")
    first_name: str = Field(..., alias="firstName")
    middle_name: str = Field(..., alias="middleName")
    last_name: str = Field(..., alias="lastName")
    birth_date: date = Field(..., alias="birthDate")
    passport: str
    inn: Optional[str]
    snils: Optional[str]
    oms: Optional[str]
    type: str

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()
