from typing import List, ClassVar

from pydantic import conint, parse_obj_as

from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.p2p.types import Bill

MAX_INVOICES_LIMIT = 50


class GetListOfInvoices(QiwiAPIMethod[List[Bill]]):
    url: ClassVar[str] = "https://edge.qiwi.com/checkout-api/api/bill/search"
    http_method: ClassVar[str] = "GET"

    rows: conint(le=MAX_INVOICES_LIMIT, strict=True, gt=0) = MAX_INVOICES_LIMIT
    statuses: str = "READY_FOR_PAY"

    @classmethod
    def on_json_parse(cls, response: HTTPResponse) -> List[Bill]:
        return parse_obj_as(List[Bill], response.json()["bills"])
