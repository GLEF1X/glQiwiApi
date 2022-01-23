from typing import List, ClassVar


from glQiwiApi.base.api_method import APIMethod
from glQiwiApi.qiwi.clients.wallet.types import Balance


class GetAvailableBalances(APIMethod[List[Balance]]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://edge.qiwi.com/funding-sources/v2/persons/{stripped_number}/accounts/offer"
