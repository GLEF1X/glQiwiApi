from typing import Dict, ClassVar

from pydantic import Field

from glQiwiApi.base.api_method import APIMethod


class CreateNewBalance(APIMethod[Dict[str, bool]]):
    url: ClassVar[str] = "https://edge.qiwi.com/funding-sources/v2/persons/{phone_number}/accounts"
    http_method: ClassVar[str] = "POST"

    currency_alias: str = Field(..., alias="alias")
