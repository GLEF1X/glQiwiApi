from typing import ClassVar, Optional

from glQiwiApi.core.abc.api_method import APIMethod, ReturningType
from glQiwiApi.core.session.holder import HTTPResponse


class GetAccessToken(APIMethod[str]):
    http_method: ClassVar[str] = 'POST'
    url: ClassVar[str] = 'https://yoomoney.ru/oauth/token'

    code: str
    client_id: str
    grant_type: str = 'authorization_code'
    redirect_uri: str = 'https://example.com'
    client_secret: Optional[str] = None

    @classmethod
    def on_json_parse(cls, response: HTTPResponse) -> str:
        return response.json()['access_token']
