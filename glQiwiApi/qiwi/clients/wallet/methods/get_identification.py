from typing import ClassVar

from glQiwiApi.base.api_method import APIMethod
from glQiwiApi.qiwi.clients.wallet.types import Identification


class GetIdentification(APIMethod[Identification]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://edge.qiwi.com/identification/v1/persons/{phone_number}/identification"
