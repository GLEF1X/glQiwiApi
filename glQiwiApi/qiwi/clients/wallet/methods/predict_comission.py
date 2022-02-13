from typing import ClassVar, Dict, Any, Union, Optional

from pydantic import Field

from glQiwiApi.core.abc.api_method import RuntimeValue
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import Commission


class PredictCommission(QiwiAPIMethod[Commission]):
    http_method: ClassVar[str] = "POST"
    url: ClassVar[str] = "https://edge.qiwi.com/sinap/providers/{private_card_id}/onlineCommission"

    json_payload_schema: ClassVar[Dict[str, Any]] = {
        "account": RuntimeValue(),
        "paymentMethod": {"type": "Account", "accountId": "643"},
        "purchaseTotals": {"total": {"amount": RuntimeValue(), "currency": "643"}},
    }

    private_card_id: str = Field(..., path_runtime_value=True)

    invoice_amount: Union[str, int, float] = Field(..., scheme_path="purchaseTotals.total.amount")
    to_account: str = Field(..., scheme_path="account")
