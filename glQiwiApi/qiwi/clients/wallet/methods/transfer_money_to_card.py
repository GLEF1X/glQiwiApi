import time
from typing import Any, ClassVar, Dict, Union

from pydantic import Field

from glQiwiApi.core.abc.api_method import Request, RuntimeValue
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import PaymentInfo


class TransferMoneyToCard(QiwiAPIMethod[PaymentInfo]):
    http_method: ClassVar[str] = 'POST'
    url: ClassVar[str] = 'https://edge.qiwi.com/sinap/api/v2/terms/{private_card_id}/payments'

    json_payload_schema: ClassVar[Dict[str, Any]] = {
        'id': RuntimeValue(default_factory=lambda: str(int(time.time() * 1000))),
        'sum': {'amount': RuntimeValue(), 'currency': '643'},
        'paymentMethod': {'type': 'Account', 'accountId': '643'},
        'fields': {'account': RuntimeValue()},
    }

    private_card_id: str = Field(..., path_runtime_value=True)
    amount: float = Field(..., scheme_path='sum.amount')
    card_number: str = Field(..., scheme_path='fields.account')
    kwargs: Dict[str, Any] = {}  # parameters for cards with ID 1960, 21012

    def build_request(self, **url_format_kw: Any) -> 'Request':
        request_schema = self._get_filled_json_payload_schema()
        request_schema['fields'].update(**self.kwargs)
        return Request(
            json_payload=request_schema,
            endpoint=self.url.format(**url_format_kw, **self._get_runtime_path_values()),
            http_method=self.http_method,
        )
