from typing import ClassVar, List

from glQiwiApi.base.api_method import APIMethod
from glQiwiApi.qiwi.clients.wallet.types.restriction import Restriction


class GetRestrictions(APIMethod[List[Restriction]]):
    url: ClassVar[str] = "https://edge.qiwi.com/person-profile/v1/persons/{phone_number}/status/restrictions"
    http_method: ClassVar[str] = "GET"
