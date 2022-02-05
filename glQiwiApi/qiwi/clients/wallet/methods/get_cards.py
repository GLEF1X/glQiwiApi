from typing import List, ClassVar

from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import Card


class GetBoundedCards(QiwiAPIMethod[List[Card]]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://edge.qiwi.com/cards/v1/cards"
