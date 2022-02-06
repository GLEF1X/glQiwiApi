from typing import ClassVar

from glQiwiApi.core.abc.api_method import APIMethod
from glQiwiApi.yoo_money.types import AccountInfo


class RetrieveAccountInfo(APIMethod[AccountInfo]):
    http_method: ClassVar[str] = "POST"
    url: ClassVar[str] = "https://yoomoney.ru/api/account-info"
