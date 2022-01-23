from typing import List, ClassVar, Any


from glQiwiApi.base.api_method import APIMethod, ReturningType
from glQiwiApi.qiwi.clients.wallet.types import CrossRate


class GetCrossRates(APIMethod[List[CrossRate]]):
    url: ClassVar[str] = "https://edge.qiwi.com/sinap/crossRates"
    http_method: ClassVar[str] = "GET"

    @classmethod
    def parse_response(cls, obj: Any) -> ReturningType:
        return super().parse_response(obj["result"])
