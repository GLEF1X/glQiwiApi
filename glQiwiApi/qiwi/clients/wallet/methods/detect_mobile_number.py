from typing import ClassVar

from glQiwiApi.qiwi.base import QiwiAPIMethod


class DetectMobileNumber(QiwiAPIMethod[str]):
    url: ClassVar[str] = "https://qiwi.com/mobile/detect.action"
    http_method: ClassVar[str] = "POST"

    phone_number: str
