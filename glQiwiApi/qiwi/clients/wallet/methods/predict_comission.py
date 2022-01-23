from typing import ClassVar, Dict, Any, Union, Optional


from pydantic import Field

from glQiwiApi.base.api_method import APIMethod
from glQiwiApi.qiwi.clients.wallet.types import Commission


class PredictCommission(APIMethod[Commission]):
    http_method: ClassVar[str] = "POST"
    url: ClassVar[str] = "https://edge.qiwi.com/sinap/providers/{private_card_id}/onlineCommission"

    request_schema: ClassVar[Dict[str, Any]] = {
        "account": "",
        "paymentMethod": {
            "type": "Account",
            "accountId": "643"
        },
        "purchaseTotals": {
            "total": {
                "amount": "",
                "currency": "643"
            }
        },
    }

    private_card_id: Optional[str] = Field(..., path_runtime_value=True)

    invoice_amount: Union[str, int, float] = Field(..., scheme_path="purchaseTotals.total.amount")
    to_account: str = Field(..., scheme_path="account")
