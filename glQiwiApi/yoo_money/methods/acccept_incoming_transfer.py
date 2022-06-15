from typing import ClassVar

from glQiwiApi.core.abc.api_method import APIMethod
from glQiwiApi.yoo_money.types import IncomingTransaction


class AcceptIncomingTransfer(APIMethod[IncomingTransaction]):
    http_method: ClassVar[str] = 'POST'
    url: ClassVar[str] = 'https://yoomoney.ru/api/incoming-transfer-accept'

    operation_id: str
    protection_code: str
