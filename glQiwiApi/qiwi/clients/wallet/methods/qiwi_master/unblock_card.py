from typing import Any, ClassVar, Dict

from pydantic import Field

from glQiwiApi.qiwi.base import QiwiAPIMethod


class UnblockQiwiMasterCard(QiwiAPIMethod[Dict[str, Any]]):
    url: ClassVar[
        str
    ] = 'https://edge.qiwi.com/cards/v2/persons/{phone_number}/cards/{card_id}/unblock'
    http_method: ClassVar[str] = 'GET'

    card_id: str = Field(..., path_runtime_value=True)
    phone_number: str = Field(..., path_runtime_value=True)
