from datetime import date
from typing import Optional

from pydantic import Field

from glQiwiApi.types.base import Base


class Identification(Base):
    """object: Identification"""

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
