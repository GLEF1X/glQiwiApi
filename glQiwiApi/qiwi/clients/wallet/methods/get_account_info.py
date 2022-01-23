from typing import ClassVar


from glQiwiApi.base.api_method import APIMethod
from glQiwiApi.qiwi.clients.wallet.types import QiwiAccountInfo


class GetAccountInfo(APIMethod[QiwiAccountInfo]):
    url: ClassVar[str] = "https://edge.qiwi.com/person-profile/v1/profile/current"
    http_method: ClassVar[str] = "GET"

