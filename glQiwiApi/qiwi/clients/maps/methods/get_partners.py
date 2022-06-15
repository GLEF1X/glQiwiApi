from typing import ClassVar, List

from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import Partner


class GetPartners(QiwiAPIMethod[List[Partner]]):
    url: ClassVar[str] = 'http://edge.qiwi.com/locator/v3/ttp-groups'
    http_method: ClassVar[str] = 'GET'
