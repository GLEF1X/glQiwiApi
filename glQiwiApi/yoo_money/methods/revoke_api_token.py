from typing import Any, Dict, ClassVar

from glQiwiApi.base.api_method import APIMethod, ReturningType


class RevokeAPIToken(APIMethod[Dict[Any, Any]]):
    http_method: ClassVar[str] = "POST"
    url: ClassVar[str] = "https://yoomoney.ru/api/revoke"

    @classmethod
    def parse_response(cls, obj: Any) -> ReturningType:
        return {}
