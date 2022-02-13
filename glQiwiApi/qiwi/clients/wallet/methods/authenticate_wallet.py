from typing import Any, Dict, ClassVar, Optional

from pydantic import Field

from glQiwiApi.qiwi.base import QiwiAPIMethod


class AuthenticateWallet(QiwiAPIMethod[Dict[str, Any]]):
    url: ClassVar[
        str
    ] = "https://edge.qiwi.com/identification/v1/persons/{phone_number}/identification"
    http_method: ClassVar[str] = "POST"

    passport: str
    birth_date: str = Field(..., alias="birthDate")
    first_name: str = Field(..., alias="firstName")
    middle_name: str = Field(..., alias="middleName")
    last_name: str = Field(..., alias="lastName")
    inn: str = ""
    snils: str = ""
    oms: str = ""
