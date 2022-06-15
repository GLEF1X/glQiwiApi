from typing import Any, ClassVar, Dict, Union

from pydantic import Field

from glQiwiApi.core.abc.api_method import Request
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.p2p.types import RefundedBill
from glQiwiApi.types.amount import PlainAmount


class RefundBill(QiwiAPIMethod[RefundedBill]):
    http_method: ClassVar[str] = 'POST'
    url: ClassVar[str] = 'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}/refunds/{refund_id}'

    bill_id: str = Field(..., path_runtime_value=True)
    refund_id: str = Field(..., path_runtime_value=True)

    json_bill_data: Union[PlainAmount, Dict[str, Union[str, int]]]

    def build_request(self, **url_format_kw: Any) -> 'Request':
        json_payload = self.json_bill_data
        if isinstance(self.json_bill_data, PlainAmount):
            json_payload = self.json_bill_data.json(encoder=self.Config.json_dumps)  # type: ignore

        return Request(
            endpoint=self.url.format(**url_format_kw, **self._get_runtime_path_values()),
            json_payload=json_payload,
            http_method=self.http_method,
        )
