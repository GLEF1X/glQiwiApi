from http import HTTPStatus
from typing import Dict, ClassVar, Any, Sequence

from pydantic import Field

from glQiwiApi.core.abc.api_method import Request
from glQiwiApi.qiwi.base import QiwiAPIMethod


class CreateNewBalance(QiwiAPIMethod[Dict[str, Any]]):
    url: ClassVar[str] = "https://edge.qiwi.com/funding-sources/v2/persons/{phone_number}/accounts"
    http_method: ClassVar[str] = "POST"
    arbitrary_allowed_response_status_codes: ClassVar[Sequence[int]] = [HTTPStatus.CREATED]

    currency_alias: str = Field(..., alias="alias")

    def build_request(self, **url_format_kw: Any) -> "Request":
        return Request(
            endpoint=self.url.format(**url_format_kw, **self._get_runtime_path_values()),
            http_method=self.http_method,
            json_payload={"alias": self.currency_alias},
        )
