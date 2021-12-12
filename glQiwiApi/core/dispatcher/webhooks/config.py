from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from aiohttp import web

from glQiwiApi.utils.certificates import SSLCertificate

DEFAULT_QIWI_WEBHOOK_PATH = "/webhooks/qiwi/"
DEFAULT_QIWI_ROUTE_NAME = "QIWI"

DEFAULT_QIWI_BILLS_WEBHOOK_PATH = "/webhooks/qiwi/bills/"
DEFAULT_QIWI_BILLS_ROUTE_NAME = "QIWI_BILLS"


@dataclass()
class ApplicationConfig:
    base_app: Optional[web.Application] = None

    host: str = "localhost"
    "server host"

    port: int = 8080
    "server port that open for tcp/ip trans."

    ssl_certificate: Optional[SSLCertificate] = None

    kwargs: Dict[Any, Any] = field(default_factory=dict)


@dataclass()
class RoutesConfig:
    p2p_path: str = DEFAULT_QIWI_WEBHOOK_PATH
    standard_qiwi_hook_path: str = DEFAULT_QIWI_BILLS_WEBHOOK_PATH

    p2p_view_route_name: str = DEFAULT_QIWI_BILLS_ROUTE_NAME
    standard_qiwi_route_name: str = DEFAULT_QIWI_ROUTE_NAME


@dataclass()
class EncryptionConfig:
    secret_p2p_key: Optional[str] = None  # taken from QiwiWrapper instance by default
    base64_encryption_key: Optional[str] = None  # taken from QIWI API using QiwiWrapper instance by default


@dataclass
class WebhookConfig:
    app: ApplicationConfig = ApplicationConfig()
    routes: RoutesConfig = RoutesConfig()
    encryption: EncryptionConfig = EncryptionConfig()
