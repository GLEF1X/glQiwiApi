from typing import ClassVar

from pydantic import Field

from glQiwiApi.qiwi.base import QiwiAPIMethod


class GetCardID(QiwiAPIMethod[str]):
    http_method: ClassVar[str] = "POST"
    url: ClassVar[str] = "https://edge.qiwi.com/sinap/api/v2/terms/{private_card_id}"

    card_number: str = Field(..., alias="cardNumber")
