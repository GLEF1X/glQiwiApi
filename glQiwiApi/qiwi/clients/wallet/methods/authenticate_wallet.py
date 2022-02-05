from typing import Any, Dict, ClassVar, Optional

from pydantic import Field

from glQiwiApi.qiwi.base import QiwiAPIMethod


class AuthenticateWallet(QiwiAPIMethod[Dict[Any, Any]]):
    url: ClassVar[str] = "https://edge.qiwi.com/identification/v1/persons/{phone_number}/identification"
    http_method: ClassVar[str] = "POST"

    birth_date: str = Field(..., alias="birthDate")
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    middle_name: str = Field(..., alias="middleName")
    passport: str
    oms: Optional[str] = None
    inn: Optional[str] = None
    snils: Optional[str] = None
