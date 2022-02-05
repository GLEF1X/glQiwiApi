from typing import ClassVar, Dict, Any

from pydantic import Field

from glQiwiApi.base.api_method import RuntimeValue
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import OrderDetails


class PreQIWIMasterRequest(QiwiAPIMethod[OrderDetails]):
    url: ClassVar[str] = "https://edge.qiwi.com/cards/v2/persons/{phone_number}/orders"
    http_method: ClassVar[str] = "POST"

    request_schema: ClassVar[Dict[str, Any]] = {
        "cardAlias": RuntimeValue()
    }

    card_alias: str = Field(..., schema_path="cardAlias")
