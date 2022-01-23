from typing import List, ClassVar, Any


from pydantic import conint

from glQiwiApi.base.api_method import APIMethod, ReturningType
from glQiwiApi.qiwi.clients.p2p.types import Bill

MAX_INVOICES_LIMIT = 50


class GetListOfInvoices(APIMethod[List[Bill]]):
    url: ClassVar[str] = "https://edge.qiwi.com/checkout-api/api/bill/search"
    http_method: ClassVar[str] = "GET"

    rows: conint(le=MAX_INVOICES_LIMIT, strict=True, gt=0) = MAX_INVOICES_LIMIT
    statuses: str = 'READY_FOR_PAY'

    @classmethod
    def parse_response(cls, obj: Any) -> ReturningType:
        return super().parse_response(obj["bills"])