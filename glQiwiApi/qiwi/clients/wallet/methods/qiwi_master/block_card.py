import http
from typing import Any, ClassVar, Dict, Sequence

from pydantic import Field

from glQiwiApi.core.abc.api_method import ReturningType
from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.base import QiwiAPIMethod


class BlockQiwiMasterCard(QiwiAPIMethod[Dict[str, Any]]):
    url: ClassVar[str] = '/cards/v2/persons/{phone_number}/cards/{card_id}/block'
    http_method: ClassVar[str] = 'GET'

    arbitrary_allowed_response_status_codes: ClassVar[Sequence[int]] = (http.HTTPStatus.ACCEPTED,)

    card_id: str = Field(..., path_runtime_value=True)
    phone_number: str = Field(..., path_runtime_value=True)

    @classmethod
    def parse_http_response(cls, response: HTTPResponse) -> Dict[str, Any]:
        return {}
