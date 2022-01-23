from typing import ClassVar, List, Any

from glQiwiApi.base.api_method import APIMethod, ReturningType
from glQiwiApi.qiwi.clients.wallet.types import Balance


class GetBalances(APIMethod[List[Balance]]):
    url: ClassVar[str] = "https://edge.qiwi.com/funding-sources/v2/persons/{phone_number}/accounts"
    http_method: ClassVar[str] = "GET"

    @classmethod
    def parse_response(cls, obj: Any) -> ReturningType:
        return super().parse_response(obj["accounts"])
