from typing import ClassVar, List

from glQiwiApi.base.api_method import ReturningType
from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import Balance


class GetBalance(QiwiAPIMethod[List[Balance]]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://edge.qiwi.com/funding-sources/v2/persons/{phone_number}/accounts"

    account_number: int = 1

    @classmethod
    def parse_http_response(cls, response: HTTPResponse) -> ReturningType:
        return cls.__returning_type__.parse_obj(response.json()["accounts"])
