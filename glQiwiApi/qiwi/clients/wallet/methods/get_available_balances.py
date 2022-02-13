from typing import List, ClassVar

from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import Balance
from glQiwiApi.qiwi.clients.wallet.types.balance import AvailableBalance


class GetAvailableBalances(QiwiAPIMethod[List[AvailableBalance]]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[
        str
    ] = "https://edge.qiwi.com/funding-sources/v2/persons/{phone_number}/accounts/offer"
