from typing import ClassVar

from glQiwiApi.core.abc.api_method import APIMethod
from glQiwiApi.yoo_money.types import Payment


class ProcessPayment(APIMethod[Payment]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://yoomoney.ru/api/process-payment"

    request_id: str
    money_source: str = "wallet"
