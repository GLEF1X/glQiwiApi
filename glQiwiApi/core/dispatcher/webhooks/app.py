import typing as t

from aiohttp import web

from glQiwiApi.core.dispatcher.implementation import Dispatcher
from glQiwiApi.core.dispatcher.webhooks.config import WebhookConfig, RoutesConfig
from glQiwiApi.core.dispatcher.webhooks.services.collision_detector import HashBasedCollisionDetector
from glQiwiApi.core.dispatcher.webhooks.utils import inject_dependencies
from glQiwiApi.core.dispatcher.webhooks.views.bill_view import QiwiBillWebhookView
from glQiwiApi.core.dispatcher.webhooks.views.transaction_view import QiwiTransactionWebhookView
from glQiwiApi.types import BillWebhook, TransactionWebhook


def configure_app(
        dispatcher: Dispatcher,
        app: web.Application,
        secret_key: str,
        routes_cfg: RoutesConfig = RoutesConfig()
) -> web.Application:
    """
    Entirely configures the web app for webhooks

    :param dispatcher: dispatcher, which processing events
    :param app: aiohttp.web.Application
    :param routes_cfg:
    :param secret_key: secret p2p key
    """

    dependencies: t.Dict[str, t.Any] = {
        "dispatcher": dispatcher,
        "secret_key": secret_key,
        "collision_detector": HashBasedCollisionDetector(),
    }

    app.router.add_view(
        handler=inject_dependencies(QiwiBillWebhookView, {
            "event_cls": BillWebhook,
            **dependencies
        }),
        name=routes_cfg.p2p_view_route_name,
        path=routes_cfg.p2p_path,
    )

    app.router.add_view(
        routes_cfg.standard_qiwi_hook_path,
        handler=inject_dependencies(QiwiTransactionWebhookView, {
            "event_cls": TransactionWebhook,
            **dependencies
        }),
        name=routes_cfg.standard_qiwi_route_name
    )

    return app
