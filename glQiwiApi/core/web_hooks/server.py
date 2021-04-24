import ipaddress
import logging
import typing

from aiohttp import web
from aiohttp.web_response import Response

from glQiwiApi import types
from glQiwiApi.core.abstracts import BaseWebHookView
from glQiwiApi.core.web_hooks.handler import HandlerManager
from glQiwiApi.utils.basics import hmac_for_transaction, hmac_key
from .config import (
    DEFAULT_QIWI_WEBHOOK_PATH,
    allowed_ips,
    DEFAULT_QIWI_ROUTER_NAME,
    DEFAULT_QIWI_BILLS_ROUTER_NAME,
    DEFAULT_QIWI_BILLS_WEBHOOK_PATH,
    Path
)


def _check_ip(ip_address: str) -> bool:
    """
    Check if ip is allowed to request us
    :param ip_address: IP-address
    :return: address is allowed
    """
    address = ipaddress.IPv4Address(ip_address)
    unpacked = [ip_addr for pool in allowed_ips for ip_addr in pool]
    return address in unpacked


class QiwiWalletWebView(BaseWebHookView):
    """
    View, which processes transactions

    """

    def _check_ip(self, ip_address: str) -> bool:
        return _check_ip(ip_address)

    async def parse_update(self) -> types.WebHook:
        """
        Deserialize update and create new update class
        :return: :class:`updated.QiwiUpdate`
        """
        data = await self.request.json()
        return types.WebHook.parse_raw(data)

    async def post(self) -> Response:
        await super().post()
        return web.Response(text="ok", status=200)

    def _hash_validator(self, update: types.WebHook) -> None:
        base64_key = self.request.app.get('_base64_key')

        if update.test:
            return

        validated = hmac_for_transaction(
            webhook_key_base64=base64_key,
            amount=update.payment.sum,
            txn_hash=update.hash,
            txn_type=update.payment.type,
            txn_id=update.payment.txn_id,
            account=update.payment.account
        )

        if not validated:
            raise web.HTTPBadRequest()

    app_key_check_ip = "_qiwi_wallet_check_ip"
    app_key_handler_manager = "_qiwi_wallet_handler_manager"


class QiwiBillWebView(BaseWebHookView):
    """
    View, which processes p2p notifications


    """

    def _check_ip(self, ip_address: str) -> bool:
        return _check_ip(ip_address)

    def _hash_validator(self, update: types.Notification) -> None:
        sha256_signature = self.request.headers.get("X-Api-Signature-SHA256")
        logging.info(sha256_signature)
        _secret = self.request.app.get("_secret_key")
        answer = hmac_key(_secret, update.bill.amount,
                          update.bill.status, update.bill.bill_id,
                          update.bill.site_id)

        if answer != sha256_signature:
            raise web.HTTPBadRequest()

    async def parse_update(self) -> types.Notification:
        payload = await self.request.json()
        return types.Notification.parse_raw(payload)

    async def post(self) -> Response:
        self.validate_ip()

        update = await self.parse_update()

        # self._hash_validator(update)

        await self.handler_manager.process_event(update)
        return web.json_response(data={"error": "0"}, status=200)

    app_key_check_ip = "_qiwi_bill_check_ip"
    app_key_handler_manager = "_qiwi_bill_handler_manager"


def setup_transaction_data(
        app: web.Application,
        base64_key: str,
        handler_manager: HandlerManager,
        path: typing.Optional[str] = None
):
    app["_base64_key"] = base64_key
    app[QiwiWalletWebView.app_key_check_ip] = _check_ip
    app[QiwiWalletWebView.app_key_handler_manager] = handler_manager
    path = path or DEFAULT_QIWI_WEBHOOK_PATH
    app.router.add_view(path, QiwiWalletWebView, name=DEFAULT_QIWI_ROUTER_NAME)


def setup_bill_data(
        app: web.Application,
        secret_key: str,
        handler_manager: HandlerManager,
        path: typing.Optional[str] = None
) -> None:
    app["_secret_key"] = secret_key
    app[QiwiBillWebView.app_key_check_ip] = _check_ip
    app[QiwiBillWebView.app_key_handler_manager] = handler_manager
    app.router.add_view(
        handler=QiwiBillWebView,
        name=DEFAULT_QIWI_BILLS_ROUTER_NAME,
        path=path or DEFAULT_QIWI_BILLS_WEBHOOK_PATH
    )


def setup(
        handler_manager: HandlerManager,
        app: web.Application,
        path: typing.Optional[Path] = None,
        secret_key: typing.Optional[str] = None,
        base64_key: typing.Optional[str] = None
) -> None:
    """
    Setup web application for webhooks

    :param handler_manager: handler_manager, which processing events
    :param app: aiohttp.web.Application
    :param path: Path obj, contains two paths
    :param secret_key: secret p2p key
    :param base64_key: Base64-encoded webhook key
    """
    setup_bill_data(app, secret_key, handler_manager,
                    path.bill_path)
    setup_transaction_data(app, base64_key, handler_manager,
                           path.transaction_path)
