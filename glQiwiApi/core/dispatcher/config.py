from __future__ import annotations

import ipaddress
import typing
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from glQiwiApi.types import WebHook, Notification, Transaction  # noqa
    from glQiwiApi.core.dispatcher.dispatcher import EventHandler  # noqa

from ..builtin import TransactionFilter, BillFilter, InterceptHandler  # NOQA

DEFAULT_QIWI_WEBHOOK_PATH = "/dispatcher/qiwi/"
DEFAULT_QIWI_ROUTER_NAME = "QIWI"

DEFAULT_QIWI_BILLS_WEBHOOK_PATH = "/webhooks/qiwi/bills/"
DEFAULT_QIWI_BILLS_ROUTER_NAME = "QIWI_BILLS"

RESPONSE_TIMEOUT = 55

allowed_ips = {
    ipaddress.IPv4Network("79.142.16.0/20"),
    ipaddress.IPv4Network("195.189.100.0/22"),
    ipaddress.IPv4Network("91.232.230.0/23"),
    ipaddress.IPv4Network("91.213.51.0/24"),
}

ENUM_EXCLUDE_ATTRS = (
    '_generate_next_value_', '__module__', '__doc__', '_member_names_', '_member_map_',
    '_member_type_', '_value2member_map_', '__new__'
)


@dataclass(frozen=True)
class Path:
    bill_path: typing.Optional[str] = None
    transaction_path: typing.Optional[str] = None


E = typing.TypeVar("E")
CF = typing.Callable[[E], typing.Union[typing.Awaitable[bool], bool]]

__all__ = (
    "DEFAULT_QIWI_WEBHOOK_PATH",
    "DEFAULT_QIWI_ROUTER_NAME",
    "DEFAULT_QIWI_BILLS_WEBHOOK_PATH",
    "DEFAULT_QIWI_BILLS_ROUTER_NAME",
    "RESPONSE_TIMEOUT",
    "ENUM_EXCLUDE_ATTRS",
    "allowed_ips",
    "Path",
    "CF",
)
