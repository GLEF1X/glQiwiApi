import typing

from aiohttp import web

from glQiwiApi.builtin import BaseProxy
from glQiwiApi.core.dispatcher.implementation import Dispatcher
from glQiwiApi.core.dispatcher.webhooks.config import (
    DEFAULT_QIWI_WEBHOOK_PATH,
    DEFAULT_QIWI_ROUTER_NAME,
    DEFAULT_QIWI_BILLS_ROUTER_NAME,
    DEFAULT_QIWI_BILLS_WEBHOOK_PATH,
    Path,
)
from glQiwiApi.core.dispatcher.webhooks.utils import check_ip
from glQiwiApi.core.dispatcher.webhooks.views.bill_view import QiwiBillWebView
from glQiwiApi.core.dispatcher.webhooks.views.transaction_view import QiwiWebHookWebView


def configure_transaction_view(
        app: web.Application,
        dispatcher: Dispatcher,
        path: typing.Optional[Path] = None,
) -> None:
    app[QiwiWebHookWebView.app_key_check_ip] = check_ip
    app[QiwiWebHookWebView.app_key_dispatcher] = dispatcher
    if isinstance(path, Path):
        txn_path = path.transaction_path
    else:
        txn_path = DEFAULT_QIWI_WEBHOOK_PATH
    app.router.add_view(
        typing.cast(str, txn_path), QiwiWebHookWebView, name=DEFAULT_QIWI_ROUTER_NAME
    )


def configure_bill_view(
        app: web.Application,
        secret_key: typing.Optional[str],
        dispatcher: Dispatcher,
        path: typing.Optional[Path] = None,
) -> None:
    app["_secret_key"] = secret_key
    app[QiwiBillWebView.app_key_check_ip] = check_ip
    app[QiwiBillWebView.app_key_dispatcher] = dispatcher
    if isinstance(path, Path):
        bill_path = path.bill_path
    else:
        bill_path = DEFAULT_QIWI_BILLS_WEBHOOK_PATH
    app.router.add_view(
        handler=QiwiBillWebView,
        name=DEFAULT_QIWI_BILLS_ROUTER_NAME,
        path=typing.cast(str, bill_path),
    )


def configure_app(
        dispatcher: Dispatcher,
        app: web.Application,
        path: typing.Optional[Path] = None,
        secret_key: typing.Optional[str] = None,
        tg_app: typing.Optional[BaseProxy] = None,
) -> web.Application:
    """
    Entirely configures the web app for webhooks

    :param dispatcher: dispatcher, which processing events
    :param app: aiohttp.web.Application
    :param path: Path obj, contains two paths
    :param secret_key: secret p2p key
    :param tg_app:
    """

    configure_bill_view(app, secret_key, dispatcher, path)
    configure_transaction_view(app, dispatcher, path)
    _setup_tg_proxy(tg_app, app)
    return app


def _setup_tg_proxy(tg_app: typing.Optional[BaseProxy], app: web.Application) -> None:
    """
    Function, which setup tg proxy application to main webapp

    :param tg_app: BaseTelegramProxy subclass or builtin
    :param app: main application
    """
    if tg_app is not None:
        if not isinstance(tg_app, BaseProxy):
            raise TypeError(
                "Invalid telegram proxy. Expected"
                f"class that inherit from the parent `BaseProxy`, got {type(tg_app)}"
            )
        tg_app.setup(app=app)
