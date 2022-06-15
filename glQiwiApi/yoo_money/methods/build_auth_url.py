import re
from typing import Any, ClassVar, List, cast

from glQiwiApi.core.abc.api_method import APIMethod, Request, ReturningType
from glQiwiApi.core.session.holder import HTTPResponse

YOO_MONEY_LINK_REGEXP = re.compile(r'https://yoomoney.ru/oauth2/authorize[?]requestid[=]\w+')


class BuildAuthURL(APIMethod[str]):
    http_method: ClassVar[str] = 'POST'
    url: ClassVar[str] = 'https://yoomoney.ru/oauth/authorize'

    client_id: str
    scopes: List[str]
    redirect_uri: str
    response_type: str = 'code'

    def build_request(self, **url_format_kw: Any) -> 'Request':
        return Request(
            endpoint=self.url.format(**url_format_kw, **self._get_runtime_path_values()),
            http_method=self.http_method,
            data={
                'client_id': self.client_id,
                'response_type': 'code',
                'redirect_uri': self.redirect_uri,
                'scope': ' '.join(self.scopes),
            },
        )

    @classmethod
    def parse_http_response(cls, response: HTTPResponse) -> ReturningType:
        try:
            return cast(
                str, re.findall(YOO_MONEY_LINK_REGEXP, response.body.decode('utf-8'))[0]
            )  # pragma: no cover
        except IndexError:
            raise Exception(
                'Could not find the authorization link in the response from '
                'the api, check the client_id value'
            )
