import ipaddress
import typing
from dataclasses import dataclass

DEFAULT_QIWI_WEBHOOK_PATH = "/web_hooks/qiwi/"
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


@dataclass(frozen=True)
class Path:
    bill_path: typing.Optional[str] = None
    transaction_path: typing.Optional[str] = None


E = typing.TypeVar("E")
EventFilter = typing.Callable[[E], bool]
EventHandlerFunctor = typing.Callable[[E], typing.Awaitable[typing.Any]]
CF = typing.Callable[[E], typing.Union[typing.Awaitable[bool], bool]]


__all__ = (
    'DEFAULT_QIWI_WEBHOOK_PATH',
    'DEFAULT_QIWI_ROUTER_NAME',
    'DEFAULT_QIWI_BILLS_WEBHOOK_PATH',
    'DEFAULT_QIWI_BILLS_ROUTER_NAME',
    'RESPONSE_TIMEOUT',
    'allowed_ips',
    'Path',
    'E',
    'EventFilter',
    'EventHandlerFunctor',
    'CF'
)
