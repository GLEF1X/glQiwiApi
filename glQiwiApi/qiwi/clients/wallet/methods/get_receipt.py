from typing import ClassVar, Union

from pydantic import Field

from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import TransactionType
from glQiwiApi.types.arbitrary import BinaryIOInput, File


class GetReceipt(QiwiAPIMethod[File]):
    url: ClassVar[
        str
    ] = 'https://edge.qiwi.com/payment-history/v1/transactions/{transaction_id}/cheque/file'
    http_method: ClassVar[str] = 'GET'

    transaction_id: Union[str, int] = Field(..., path_runtime_value=True)
    transaction_type: TransactionType = Field(..., alias='type')
    file_format: str = Field(alias='format', default='PDF')

    class Config:
        use_enum_values = True

    @classmethod
    def parse_http_response(cls, response: HTTPResponse) -> File:  # type: ignore
        return File(BinaryIOInput.from_bytes(response.body))
