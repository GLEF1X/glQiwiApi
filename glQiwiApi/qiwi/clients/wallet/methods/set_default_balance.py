from typing import Any, Dict, ClassVar

from glQiwiApi.base.api_method import APIMethod, Request


class SetDefaultBalance(APIMethod[Dict[Any, Any]]):
    http_method: ClassVar[str] = "PATCH"
    url: ClassVar[str] = "https://edge.qiwi.com/funding-sources/v2/persons/{stripped_number}/accounts/{c_alias}"

    currency_alias: str

    def build_request(self, **url_format_kw: Any) -> Request:
        return super().build_request(**url_format_kw, c_alias=self.currency_alias)
