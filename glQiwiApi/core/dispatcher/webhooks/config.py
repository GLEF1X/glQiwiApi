from __future__ import annotations

import ipaddress
import typing
from dataclasses import dataclass

from glQiwiApi.builtin import TransactionFilter, BillFilter, InterceptHandler  # NOQA

DEFAULT_QIWI_WEBHOOK_PATH = "/webhooks/qiwi/"
DEFAULT_QIWI_ROUTER_NAME = "QIWI"

DEFAULT_QIWI_BILLS_WEBHOOK_PATH = "/webhooks/qiwi/bills/"
DEFAULT_QIWI_BILLS_ROUTER_NAME = "QIWI_BILLS"

RESPONSE_TIMEOUT = 55

ALLOWED_IPS = {
    ipaddress.IPv4Network("79.142.16.0/20"),
    ipaddress.IPv4Network("195.189.100.0/22"),
    ipaddress.IPv4Network("91.232.230.0/23"),
    ipaddress.IPv4Network("91.213.51.0/24"),
}


@dataclass(frozen=True)
class Path:
    bill_path: typing.Optional[str] = None
    transaction_path: typing.Optional[str] = None


__all__ = (
    "DEFAULT_QIWI_WEBHOOK_PATH",
    "DEFAULT_QIWI_ROUTER_NAME",
    "DEFAULT_QIWI_BILLS_WEBHOOK_PATH",
    "DEFAULT_QIWI_BILLS_ROUTER_NAME",
    "RESPONSE_TIMEOUT",
    "ALLOWED_IPS",
    "Path",
)
