import re
from typing import List, Any, cast, ClassVar

from glQiwiApi.base.api_method import APIMethod, Request, ReturningType

YOO_MONEY_LINK_REGEXP = re.compile(r"https://yoomoney.ru/oauth2/authorize[?]requestid[=]\w+")


class BuildAuthURL(APIMethod[str]):
    http_method: ClassVar[str] = "POST"
    url: ClassVar[str] = "https://yoomoney.ru/oauth/authorize"

    client_id: str
    scopes: List[str]
    redirect_uri: str
    response_type: str = "code"

    def build_request(self, **url_format_kw: Any) -> "Request":
        return Request(
            endpoint=self.url.format(**url_format_kw, **self._get_runtime_path_values()),
            http_method=self.http_method,
            data={
                "client_id": self.client_id,
                "response_type": "code",
                "redirect_uri": self.redirect_uri,
                "scope": " ".join(self.scopes),
            }
        )

    @classmethod
    def parse_response(cls, obj: Any) -> ReturningType:
        try:
            return cast(str, re.findall(YOO_MONEY_LINK_REGEXP, obj)[0])  # pragma: no cover
        except IndexError:
            raise Exception(
                "Could not find the authorization link in the response from "
                "the api, check the client_id value"
            )
