from typing import ClassVar, Union

from glQiwiApi.core.abc.api_method import APIMethod
from glQiwiApi.yoo_money.types import OperationDetails


class OperationDetailsMethod(APIMethod[OperationDetails]):
    http_method: ClassVar[str] = "POST"
    url: ClassVar[str] = "https://yoomoney.ru/api/operation-details"

    operation_id: Union[int, str]
