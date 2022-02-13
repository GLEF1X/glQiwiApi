from typing import ClassVar

from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types.nickname import NickName


class GetNickName(QiwiAPIMethod[NickName]):
    url: ClassVar[str] = "https://edge.qiwi.com/qw-nicknames/v1/persons/{phone_number}/nickname"
    http_method: ClassVar[str] = "GET"
