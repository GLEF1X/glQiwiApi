from json import JSONDecodeError
from typing import ClassVar, Any

from pydantic import Field

from glQiwiApi.core.abc.api_method import ReturningType, Request
from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.exceptions import QiwiAPIError

try:
    from orjson import JSONDecodeError as OrjsonDecodeError
except ImportError:
    from json import JSONDecodeError as OrjsonDecodeError  # type: ignore


class RevealCardID(QiwiAPIMethod[str]):
    http_method: ClassVar[str] = "POST"
    url: ClassVar[str] = "https://qiwi.com/card/detect.action"

    card_number: str = Field(..., alias="cardNumber")

    @classmethod
    def parse_http_response(cls, response: HTTPResponse) -> str:
        try:
            return response.json()["message"]
        except (JSONDecodeError, TypeError, OrjsonDecodeError):
            QiwiAPIError(response).raise_exception_matching_error_code()

    def build_request(self, **url_format_kw: Any) -> "Request":
        r = super().build_request(**url_format_kw)
        r.headers["Content-Type"] = "application/x-www-form-urlencoded"
        return r
