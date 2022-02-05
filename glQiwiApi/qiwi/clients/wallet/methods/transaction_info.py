from typing import ClassVar


from pydantic import Field

from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import Transaction, TransactionType


class GetTransactionInfo(QiwiAPIMethod[Transaction]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://edge.qiwi.com/payment-history/v1/transactions/{transaction_id}"

    transaction_id: int
    transaction_type: TransactionType = Field(..., alias="type")

    class Config:
        use_enum_values = True
