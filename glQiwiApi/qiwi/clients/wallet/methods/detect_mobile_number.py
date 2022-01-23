from typing import ClassVar

from glQiwiApi.base.api_method import APIMethod


class DetectMobileNumber(APIMethod[str]):
    url: ClassVar[str] = "https://qiwi.com/mobile/detect.action"
    http_method: ClassVar[str] = "POST"

    phone_number: str
