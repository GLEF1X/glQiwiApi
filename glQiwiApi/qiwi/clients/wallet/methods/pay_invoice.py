from typing import ClassVar, Dict, Any

from pydantic import Field

from glQiwiApi.base.api_method import APIMethod, RuntimeValue
from glQiwiApi.qiwi.clients.p2p.types import InvoiceStatus


class PayInvoice(APIMethod[InvoiceStatus]):
    url: ClassVar[str] = "https://edge.qiwi.com/checkout-api/api/bill/search"
    http_method: ClassVar[str] = "POST"

    request_schema: ClassVar[Dict[str, Any]] = {
        "invoice_uid": RuntimeValue(),
        "currency": RuntimeValue()
    }

    invoice_uid: str = Field(..., schema_path="invoice_uid")
    currency: str = Field(..., schema_path="currency")
