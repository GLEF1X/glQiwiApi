from typing import List, ClassVar


from glQiwiApi.base.api_method import APIMethod
from glQiwiApi.qiwi.clients.wallet.types import Card


class GetBoundedCards(APIMethod[List[Card]]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://edge.qiwi.com/cards/v1/cards"
