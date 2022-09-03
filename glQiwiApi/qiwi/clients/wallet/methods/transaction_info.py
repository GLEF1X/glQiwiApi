from typing import Any, ClassVar

from pydantic import Field

from glQiwiApi.core.abc.api_method import Request
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import Transaction, TransactionType


class GetTransactionInfo(QiwiAPIMethod[Transaction]):
    http_method: ClassVar[str] = 'GET'
    url: ClassVar[str] = 'https://edge.qiwi.com/payment-history/v1/transactions/{transaction_id}'

    transaction_id: int
    transaction_type: TransactionType = Field(..., alias='type')

    def build_request(self, **url_format_kw: Any) -> 'Request':
        return super().build_request(**url_format_kw, transaction_id=self.transaction_id)

    class Config:
        use_enum_values = True
