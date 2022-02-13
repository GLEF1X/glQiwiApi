from datetime import datetime
from typing import ClassVar

from pydantic import Field

from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.types.arbitrary import File, BinaryIOInput


class GetQiwiMasterStatement(QiwiAPIMethod[File]):
    url: ClassVar[
        str
    ] = "https://edge.qiwi.com/payment-history/v1/persons/{phone_number}/cards/{card_id}/statement"
    http_method: ClassVar[str] = "GET"

    card_id: str = Field(..., path_runtime_value=True)
    from_date: datetime = Field(..., alias="from")
    till_date: datetime = Field(..., alias="till")

    @classmethod
    def parse_http_response(cls, response: HTTPResponse) -> File:  # type: ignore
        return File(BinaryIOInput.from_bytes(response.body))
