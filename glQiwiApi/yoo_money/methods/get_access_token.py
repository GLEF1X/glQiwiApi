from typing import ClassVar, Optional, Any

from glQiwiApi.base.api_method import APIMethod, ReturningType


class GetAccessToken(APIMethod[str]):
    http_method: ClassVar[str] = "POST"
    url: ClassVar[str] = "https://yoomoney.ru/oauth/token"

    code: str
    client_id: str
    grant_type: str = "authorization_code"
    redirect_uri: str = "https://example.com"
    client_secret: Optional[str] = None

    @classmethod
    def parse_response(cls, obj: Any) -> ReturningType:
        return obj["access_token"]
