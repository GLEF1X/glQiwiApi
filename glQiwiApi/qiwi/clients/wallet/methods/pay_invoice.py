from typing import Any, ClassVar, Dict

from pydantic import Field

from glQiwiApi.core.abc.api_method import RuntimeValue
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.p2p.types import InvoiceStatus


class PayInvoice(QiwiAPIMethod[InvoiceStatus]):
    url: ClassVar[str] = 'https://edge.qiwi.com/checkout-api/invoice/pay/wallet'
    http_method: ClassVar[str] = 'POST'

    json_payload_schema: ClassVar[Dict[str, Any]] = {
        'invoice_uid': RuntimeValue(),
        'currency': RuntimeValue(),
    }

    invoice_uid: str = Field(..., schema_path='invoice_uid')
    currency: str = Field(..., schema_path='currency')
