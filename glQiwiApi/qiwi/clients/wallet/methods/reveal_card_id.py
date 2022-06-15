from json import JSONDecodeError
from typing import Any, ClassVar

from pydantic import Field

from glQiwiApi.core.abc.api_method import Request, ReturningType
from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.exceptions import QiwiAPIError

try:
    from orjson import JSONDecodeError as OrjsonDecodeError
except ImportError:
    from json import JSONDecodeError as OrjsonDecodeError  # type: ignore


class RevealCardID(QiwiAPIMethod[str]):
    http_method: ClassVar[str] = 'POST'
    url: ClassVar[str] = 'https://qiwi.com/card/detect.action'

    card_number: str = Field(..., alias='cardNumber')

    @classmethod
    def on_json_parse(cls, response: HTTPResponse) -> str:
        return response.json()['message']

    def build_request(self, **url_format_kw: Any) -> 'Request':
        r = super().build_request(**url_format_kw)
        r.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        return r
