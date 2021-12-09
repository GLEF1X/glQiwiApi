from __future__ import annotations

import ssl
from dataclasses import dataclass
from typing import Optional

from aiohttp import web

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

    ssl_context: ssl.SSLContext = ssl.SSLContext()


@dataclass()
class RoutesConfig:
    p2p_path: str = DEFAULT_QIWI_WEBHOOK_PATH
    standard_qiwi_hook_path: str = DEFAULT_QIWI_BILLS_WEBHOOK_PATH

    p2p_view_route_name: str = DEFAULT_QIWI_BILLS_ROUTE_NAME
    standard_qiwi_route_name: str = DEFAULT_QIWI_ROUTE_NAME


@dataclass
class WebhookConfig:
    app_cfg: ApplicationConfig = ApplicationConfig()
    routes: RoutesConfig = RoutesConfig()
