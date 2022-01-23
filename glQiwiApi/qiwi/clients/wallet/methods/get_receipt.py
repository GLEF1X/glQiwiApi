from typing import ClassVar, Union, Any

from pydantic import Field, ValidationError

from glQiwiApi.base.api_method import APIMethod, Request, ReturningType
from glQiwiApi.base.types.arbitrary import File, BinaryIOInput
from glQiwiApi.base.types.errors import QiwiErrorAnswer
from glQiwiApi.qiwi.clients.wallet.types import TransactionType
from glQiwiApi.qiwi.exceptions import ChequeIsNotAvailable


class GetReceipt(APIMethod[File]):
    url: ClassVar[str] = "https://edge.qiwi.com/payment-history/v1/transactions/{transaction_id}/cheque/file"
    http_method: ClassVar[str] = "GET"

    transaction_id: Union[str, int]
    transaction_type: TransactionType = Field(..., alias="type")
    file_format: str = Field(alias="format", default="PDF")

    def build_request(self, **url_format_kw: Any) -> Request:
        return Request(
            endpoint=self.url.format(**url_format_kw),
            params=self.dict(exclude_none=True),
            http_method=self.http_method
        )

    @classmethod
    def parse_response(cls, obj: Any) -> ReturningType:
        try:
            err_model = QiwiErrorAnswer.parse_raw(obj)
            raise ChequeIsNotAvailable(err_model)
        except ValidationError:
            return File(BinaryIOInput.from_bytes(obj))
