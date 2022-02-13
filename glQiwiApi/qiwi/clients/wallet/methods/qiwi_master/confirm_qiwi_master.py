from typing import ClassVar

from pydantic import Field

from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types.qiwi_master import OrderDetails


class ConfirmQiwiMasterPurchaseOrder(QiwiAPIMethod[OrderDetails]):
    url: ClassVar[
        str
    ] = "https://edge.qiwi.com/cards/v2/persons/{phone_number}/orders/{order_id}/submit"
    http_method: ClassVar[str] = "PUT"

    order_id: str = Field(..., path_runtime_value=True)
