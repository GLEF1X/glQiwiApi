from __future__ import annotations

from aiohttp import web
from pydantic import ValidationError

from glQiwiApi import types
from glQiwiApi.core.dispatcher.webhooks.base import BaseWebHookView
from glQiwiApi.core.dispatcher.webhooks.utils import check_ip
from glQiwiApi.utils.api_helper import hmac_key


class QiwiBillWebView(BaseWebHookView[types.Notification]):
    """
    View, which processes p2p notifications


    """

    def _check_ip(self, ip_address: str) -> bool:
        return check_ip(ip_address)

    def _hash_validator(self, update: types.Notification) -> None:
        if update.bill is None:
            return None

        sha256_signature = self.request.headers.get("X-Api-Signature-SHA256")
        _secret = self.request.app.get("_secret_key")
        bill = update.bill
        answer = hmac_key(_secret, bill.amount, bill.status, bill.bill_id, bill.site_id)

        if answer != sha256_signature:
            raise web.HTTPBadRequest()

    async def parse_update(self) -> types.Notification:
        payload = await self.request.json()
        try:
            return types.Notification.parse_raw(payload)
        except ValidationError as ex:
            raise web.HTTPBadRequest(text=ex.json())

    async def post(self) -> web.Response:
        self.validate_ip()

        update = await self.parse_update()

        # self._hash_validator(update)

        await self.handler_manager.feed_event(update)
        return web.json_response(data={"error": "0"})

    app_key_check_ip = "_qiwi_bill_check_ip"
    app_key_handler_manager = "_qiwi_bill_handler_manager"
