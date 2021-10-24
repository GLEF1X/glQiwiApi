from __future__ import annotations

from typing import cast

from aiohttp import web

from glQiwiApi import types
from glQiwiApi.core.dispatcher.webhooks.base import BaseWebHookView
from glQiwiApi.types.exceptions import WebhookSignatureUnverified


class QiwiBillWebView(BaseWebHookView[types.Notification]):
    """View, which processes p2p notifications"""
    _event_type = types.Notification

    def _validate_event_signature(self, update: types.Notification) -> None:
        sha256_signature = cast(str, self.request.headers.get("X-Api-Signature-SHA256"))
        webhook_base64 = cast(str, self.request.app.get("_secret_key"))

        try:
            update.verify_signature(sha256_signature, webhook_base64)
        except WebhookSignatureUnverified:
            self.dispatcher.logger.warning(
                "Blocking request due to invalid signature of payload."
            )
            raise web.HTTPBadRequest()

    def ok_response(self) -> web.Response:
        return web.json_response(data={"error": "0"})

    app_key_check_ip = "_qiwi_bill_check_ip"
    app_key_dispatcher = "_qiwi_bill_dispatcher"
