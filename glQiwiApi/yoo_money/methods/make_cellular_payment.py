from typing import Any, ClassVar, Dict

from pydantic import Field

from glQiwiApi.core.abc.api_method import APIMethod


class MakeCellularPayment(APIMethod[Dict[str, Any]]):
    http_method: ClassVar[str] = 'POST'
    url: ClassVar[str] = 'https://yoomoney.ru/api/operation-details'

    pattern_id: str
    phone_number: str = Field(..., alias='phone-number')
    amount: float
