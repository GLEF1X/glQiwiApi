import uuid
from typing import ClassVar, Optional

from pydantic import Field

from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types.qiwi_master import QiwiMasterCardRequisites


class GetQiwiMasterCardRequisites(QiwiAPIMethod[QiwiMasterCardRequisites]):
    http_method: ClassVar[str] = 'PUT'
    url: ClassVar[str] = 'https://edge.qiwi.com/cards/v1/cards/{card_id}/details'

    card_id: str = Field(..., path_runtime_value=True)
    operation_id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()), alias='operationId'
    )
