import ipaddress
import typing

from aiohttp import web
from aiohttp.web import Application
from aiohttp.web_response import Response

from glQiwiApi import types
from glQiwiApi.core.abstracts import BaseWebHookView
from glQiwiApi.core.web_hooks.handler import HandlerManager
from glQiwiApi.utils.basics import hmac_key

DEFAULT_QIWI_WEBHOOK_PATH = "/web_hooks/qiwi/"
DEFAULT_QIWI_ROUTER_NAME = "QIWI"

DEFAULT_QIWI_BILLS_WEBHOOK_PATH = "/webhooks/qiwi/bills/"
DEFAULT_QIWI_BILLS_ROUTER_NAME = "QIWI_BILLS"

RESPONSE_TIMEOUT = 55

allowed_ips = {
    ipaddress.ip_network("79.142.16.0/20").hosts(),
    ipaddress.ip_network("195.189.100.0/22").hosts(),
    ipaddress.ip_network("91.232.230.0/23").hosts(),
    ipaddress.ip_network("91.213.51.0/24").hosts(),
}


def _check_ip(ip: str) -> bool:
    """
    Check if ip is allowed to request us
    :param ip: IP-address
    :return: address is allowed
    """
    address = ipaddress.IPv4Address(ip)
    return address in [ip_addr for pool in allowed_ips for ip_addr in pool]


class QiwiWalletWebView(BaseWebHookView):
    def _check_ip(self, ip: str):
        return _check_ip(ip)

    async def parse_update(self) -> types.WebHook:
        """
        Deserialize update and create new update class
        :return: :class:`updated.QiwiUpdate`
        """
        data = await self.request.json()
        return types.WebHook.parse_raw(data)

    app_key_check_ip = "_qiwi_wallet_check_ip"
    app_key_handler_manager = "_qiwi_wallet_handler_manager"


class QiwiBillWebView(BaseWebHookView):

    def _check_ip(self, ip: str) -> bool:
        return _check_ip(ip)

    def _hash_validator(
            self,
            notification: types.Notification
    ) -> typing.Optional[web.HTTPBadRequest]:
        sha256_signature = self.request.headers.get("X-Api-Signature-SHA256")
        _secret = self.request.app.get("_secret_key")
        answer = hmac_key(_secret, notification.bill.amount,
                          notification.bill.status, notification.bill.bill_id,
                          notification.bill.site_id)
        if answer != sha256_signature:
            return web.HTTPBadRequest()

    async def parse_update(self) -> types.Notification:
        payload = await self.request.json()
        return types.Notification.parse_raw(payload)

    async def post(self) -> Response:
        self.validate_ip()

        notification = await self.parse_update()

        # self._hash_validator(notification)

        await self.handler_manager.process_event(notification)

        return web.json_response(data={"error": "0"}, status=200)

    app_key_check_ip = "_qiwi_bill_check_ip"
    app_key_handler_manager = "_qiwi_bill_handler_manager"


def setup(handler_manager: HandlerManager, app: Application,
          path: str = None, secret_key: typing.Optional[str] = None) -> None:
    app[QiwiWalletWebView.app_key_check_ip] = _check_ip
    app["_secret_key"] = secret_key
    app[QiwiWalletWebView.app_key_handler_manager] = handler_manager
    app[QiwiBillWebView.app_key_handler_manager] = handler_manager
    path = path or DEFAULT_QIWI_WEBHOOK_PATH
    app.router.add_view(path, QiwiWalletWebView, name=DEFAULT_QIWI_ROUTER_NAME)
    p2p_path = DEFAULT_QIWI_BILLS_WEBHOOK_PATH
    app.router.add_view(
        handler=QiwiBillWebView,
        name=DEFAULT_QIWI_BILLS_ROUTER_NAME,
        path=p2p_path
    )
