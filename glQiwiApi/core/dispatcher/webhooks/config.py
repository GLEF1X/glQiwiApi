from __future__ import annotations

import ssl
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from aiohttp import web

from glQiwiApi.utils.certificates import SSLCertificate

DEFAULT_QIWI_WEBHOOK_PATH = "/webhooks/qiwi/operation_history/"
DEFAULT_QIWI_ROUTE_NAME = "QIWI_TRANSACTIONS"

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

    @property
    def ssl_context(self) -> Optional[ssl.SSLContext]:
        if self.ssl_certificate is None:
            return None
        return self.ssl_certificate.as_ssl_context()


@dataclass()
class RoutesConfig:
    p2p_path: str = DEFAULT_QIWI_BILLS_WEBHOOK_PATH
    standard_qiwi_hook_path: str = DEFAULT_QIWI_WEBHOOK_PATH

    p2p_view_route_name: str = DEFAULT_QIWI_BILLS_ROUTE_NAME
    standard_qiwi_route_name: str = DEFAULT_QIWI_ROUTE_NAME


@dataclass()
class EncryptionConfig:
    secret_p2p_key: str
    base64_encryption_key: Optional[
        str
    ] = None  # taken from QIWI API using QiwiWallet instance by default


@dataclass()
class SecurityConfig:
    check_ip: bool = True


@dataclass()
class HookRegistrationConfig:
    host_or_ip_address: Optional[str] = None


@dataclass
class WebhookConfig:
    encryption: EncryptionConfig
    hook_registration: HookRegistrationConfig = HookRegistrationConfig()
    app: ApplicationConfig = ApplicationConfig()
    routes: RoutesConfig = RoutesConfig()
    security: SecurityConfig = SecurityConfig()
