from typing import ClassVar, Optional, Dict, Any

from pydantic import Field

from glQiwiApi.base.api_method import APIMethod, RuntimeValue
from glQiwiApi.qiwi.clients.p2p.types import PairOfP2PKeys


class CreateP2PKeyPair(APIMethod[PairOfP2PKeys]):
    http_method: ClassVar[str] = "POST"
    url: ClassVar[str] = "https://api.qiwi.com/partner/bill/v1/bills/widgets-api/api/p2p/protected/keys/create"

    request_schema: ClassVar[Dict[str, Any]] = {
        "keysPairName": RuntimeValue(),
        "serverNotificationsUrl": RuntimeValue()
    }

    key_pair_name: str = Field(..., scheme_path="keysPairName")
    server_notification_url: Optional[str] = Field(..., scheme_path="serverNotificationsUrl")