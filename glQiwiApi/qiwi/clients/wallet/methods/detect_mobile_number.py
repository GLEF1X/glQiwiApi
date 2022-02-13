from typing import ClassVar, cast

from pydantic import Field

from glQiwiApi.core.abc.api_method import ReturningType
from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types.mobile_operator import MobileOperator
from glQiwiApi.qiwi.exceptions import MobileOperatorCannotBeDeterminedError


class DetectMobileNumber(QiwiAPIMethod[MobileOperator]):
    url: ClassVar[str] = "https://qiwi.com/mobile/detect.action"
    http_method: ClassVar[str] = "POST"

    phone_number: str = Field(..., alias="phone")

    @classmethod
    def parse_http_response(cls, response: HTTPResponse) -> ReturningType:
        mobile_operator: MobileOperator = super().parse_http_response(response)
        if mobile_operator.code.value == "2" or mobile_operator.code.name == "ERROR":
            raise MobileOperatorCannotBeDeterminedError(
                response, custom_message=mobile_operator.message
            )

        return cast(ReturningType, mobile_operator)
