from typing import ClassVar

from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import Identification


class GetIdentification(QiwiAPIMethod[Identification]):
    http_method: ClassVar[str] = 'GET'
    url: ClassVar[
        str
    ] = 'https://edge.qiwi.com/identification/v1/persons/{phone_number}/identification'
