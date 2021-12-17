import typing as t

from aiohttp import web

from glQiwiApi.core.dispatcher.implementation import Dispatcher
from glQiwiApi.core.dispatcher.webhooks.config import WebhookConfig
from glQiwiApi.core.dispatcher.webhooks.middlewares.ip import ip_filter_middleware
from glQiwiApi.core.dispatcher.webhooks.services.collision_detector import (
    HashBasedCollisionDetector,
)
from glQiwiApi.core.dispatcher.webhooks.services.security.ip import IPFilter
from glQiwiApi.core.dispatcher.webhooks.utils import inject_dependencies
from glQiwiApi.core.dispatcher.webhooks.views.bill_view import QiwiBillWebhookView
from glQiwiApi.core.dispatcher.webhooks.views.transaction_view import QiwiTransactionWebhookView
from glQiwiApi.types import BillWebhook, TransactionWebhook


def configure_app(
    dispatcher: Dispatcher, app: web.Application, webhook_config: WebhookConfig
) -> web.Application:
    """
    Entirely configures the web app for webhooks.

    :param dispatcher: dispatcher, which processing events
    :param app: aiohttp.web.Application
    :param webhook_config:
    """

    generic_dependencies: t.Dict[str, t.Any] = {
        "dispatcher": dispatcher,
        "collision_detector": HashBasedCollisionDetector(),
    }

    app.router.add_view(
        handler=inject_dependencies(
            QiwiBillWebhookView,
            {
                "event_cls": BillWebhook,
                "encryption_key": webhook_config.encryption.secret_p2p_key,
                **generic_dependencies,
            },
        ),
        name=webhook_config.routes.p2p_view_route_name,
        path=webhook_config.routes.p2p_path,
    )

    app.router.add_view(
        handler=inject_dependencies(
            QiwiTransactionWebhookView,
            {
                "event_cls": TransactionWebhook,
                "encryption_key": webhook_config.encryption.base64_encryption_key,
                **generic_dependencies,
            },
        ),
        name=webhook_config.routes.standard_qiwi_route_name,
        path=webhook_config.routes.standard_qiwi_hook_path,
    )

    if webhook_config.security.check_ip:
        app.middlewares.append(ip_filter_middleware(IPFilter.default()))

    return app
