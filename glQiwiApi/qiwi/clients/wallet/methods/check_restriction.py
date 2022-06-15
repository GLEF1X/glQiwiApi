from typing import ClassVar, List

from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types.restriction import Restriction


class GetRestrictions(QiwiAPIMethod[List[Restriction]]):
    url: ClassVar[
        str
    ] = 'https://edge.qiwi.com/person-profile/v1/persons/{phone_number}/status/restrictions'
    http_method: ClassVar[str] = 'GET'
