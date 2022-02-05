from typing import ClassVar, List

from pydantic import parse_obj_as

from glQiwiApi.base.api_method import ReturningType
from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import Balance


class GetBalances(QiwiAPIMethod[List[Balance]]):
    url: ClassVar[str] = "https://edge.qiwi.com/funding-sources/v2/persons/{phone_number}/accounts"
    http_method: ClassVar[str] = "GET"

    @classmethod
    def parse_http_response(cls, response: HTTPResponse) -> ReturningType:
        return parse_obj_as(List[Balance], response.json()["accounts"])
