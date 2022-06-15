from typing import Any, ClassVar, Dict

from pydantic import Field

from glQiwiApi.core.abc.api_method import RuntimeValue
from glQiwiApi.qiwi.base import QiwiAPIMethod


class RenameQiwiMasterCard(QiwiAPIMethod[Dict[str, Any]]):
    url: ClassVar[str] = 'https://edge.qiwi.com/cards/v1/cards/{card_id}>/alias'
    http_method: ClassVar[str] = 'PUT'

    json_payload_schema = {'alias': RuntimeValue()}

    card_id: str = Field(..., path_runtime_value=True)
    alias: str
