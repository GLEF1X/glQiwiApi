from typing import ClassVar, Dict

from glQiwiApi.core.abc.api_method import APIMethod


class RejectIncomingTransfer(APIMethod[Dict[str, str]]):
    http_method: ClassVar[str] = 'POST'
    url: ClassVar[str] = 'https://yoomoney.ru/api/incoming-transfer-reject'

    operation_id: str
