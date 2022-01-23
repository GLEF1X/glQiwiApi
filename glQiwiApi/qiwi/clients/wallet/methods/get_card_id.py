from typing import ClassVar

from pydantic import Field, PaymentCardNumber

from glQiwiApi.base.api_method import APIMethod


class GetCardID(APIMethod[str]):
    http_method: ClassVar[str] = "POST"
    url: ClassVar[str] = "https://edge.qiwi.com/sinap/api/v2/terms/{private_card_id}"

    card_number: PaymentCardNumber = Field(..., alias="cardNumber")
