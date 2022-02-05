from typing import ClassVar

from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import QiwiAccountInfo


class GetAccountInfo(QiwiAPIMethod[QiwiAccountInfo]):
    url: ClassVar[str] = "https://edge.qiwi.com/person-profile/v1/profile/current"
    http_method: ClassVar[str] = "GET"
