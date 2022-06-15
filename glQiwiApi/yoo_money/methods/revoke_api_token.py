from typing import Any, ClassVar, Dict

from glQiwiApi.core.abc.api_method import APIMethod, ReturningType
from glQiwiApi.core.session.holder import HTTPResponse


class RevokeAPIToken(APIMethod[Dict[Any, Any]]):
    http_method: ClassVar[str] = 'POST'
    url: ClassVar[str] = 'https://yoomoney.ru/api/revoke'

    @classmethod
    def parse_http_response(cls, response: HTTPResponse) -> ReturningType:
        return {}
