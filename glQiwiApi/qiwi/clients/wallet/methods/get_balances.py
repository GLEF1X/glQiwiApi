from typing import ClassVar, List

from pydantic import parse_obj_as

from glQiwiApi.core.abc.api_method import ReturningType
from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import Balance


class GetBalances(QiwiAPIMethod[List[Balance]]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://edge.qiwi.com/funding-sources/v2/persons/{phone_number}/accounts"

    @classmethod
    def on_json_parse(cls, response: HTTPResponse) -> List[Balance]:
        return parse_obj_as(List[Balance], response.json()["accounts"])
