from typing import ClassVar, Optional, Union

from pydantic import Field

from glQiwiApi.core.abc.api_method import APIMethod
from glQiwiApi.yoo_money.types import RequestPaymentResponse


class RequestPayment(APIMethod[RequestPaymentResponse]):
    http_method: ClassVar[str] = "POST"
    url: ClassVar[str] = "https://yoomoney.ru/api/request-payment"

    to_account: str = Field(..., alias="to")
    amount: Union[int, float] = Field(..., alias="amount_due")
    pattern_id: str = "p2p"
    comment_for_history: Optional[str] = Field(None, alias="comment")
    comment_for_receiver: Optional[str] = Field(None, alias="message")
    protect: bool = Field(False, alias="codepro")
    expire_period: int = 1
