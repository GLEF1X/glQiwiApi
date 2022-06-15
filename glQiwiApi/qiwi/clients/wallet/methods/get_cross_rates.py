from typing import ClassVar, List

from pydantic import parse_obj_as

from glQiwiApi.core.abc.api_method import ReturningType
from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import CrossRate


class GetCrossRates(QiwiAPIMethod[List[CrossRate]]):
    url: ClassVar[str] = 'https://edge.qiwi.com/sinap/crossRates'
    http_method: ClassVar[str] = 'GET'

    @classmethod
    def on_json_parse(cls, response: HTTPResponse) -> List[CrossRate]:
        return parse_obj_as(List[CrossRate], response.json()['result'])
