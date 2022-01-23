from typing import ClassVar, List, Any


from glQiwiApi.base.api_method import APIMethod, ReturningType
from glQiwiApi.qiwi.clients.wallet.types import Balance


class GetBalance(APIMethod[List[Balance]]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://edge.qiwi.com/funding-sources/v2/persons/{phone_number}/accounts"

    account_number: int = 1

    @classmethod
    def parse_response(cls, obj: Any) -> ReturningType:
        return super().parse_response(obj['accounts'])
