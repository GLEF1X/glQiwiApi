from typing import Any, ClassVar, Dict, Optional

from pydantic import Field

from glQiwiApi.core.abc.api_method import RuntimeValue
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.p2p.types import PairOfP2PKeys


class CreateP2PKeyPair(QiwiAPIMethod[PairOfP2PKeys]):
    http_method: ClassVar[str] = 'POST'
    url: ClassVar[
        str
    ] = 'https://api.qiwi.com/partner/bill/v1/bills/widgets-api/api/p2p/protected/keys/create'

    json_payload_schema: ClassVar[Dict[str, Any]] = {
        'keysPairName': RuntimeValue(),
        'serverNotificationsUrl': RuntimeValue(),
    }

    key_pair_name: str = Field(..., scheme_path='keysPairName')
    server_notification_url: Optional[str] = Field(..., scheme_path='serverNotificationsUrl')
