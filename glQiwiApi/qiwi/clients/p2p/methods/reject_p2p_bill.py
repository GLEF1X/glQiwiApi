from typing import ClassVar

from pydantic import Field

from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.p2p.types import Bill


class RejectP2PBill(QiwiAPIMethod[Bill]):
    http_method: ClassVar[str] = 'POST'
    url: ClassVar[str] = 'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}/reject'

    bill_id: str = Field(..., path_runtime_value=True)
