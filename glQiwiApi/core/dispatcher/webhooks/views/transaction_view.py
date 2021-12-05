from __future__ import annotations

import logging
from typing import cast, Optional

from aiohttp import web

from glQiwiApi import types
from glQiwiApi.core.dispatcher.webhooks.base import BaseWebHookView
from glQiwiApi.types.exceptions import WebhookSignatureUnverified

logger = logging.getLogger("logging.webhooks.default")


class QiwiWebHookWebView(BaseWebHookView[types.WebHook]):
    """
    View, which processes transactions

    """
    _event_type = types.WebHook

    def _validate_event_signature(self, update: types.WebHook) -> None:
        base64_key = cast(Optional[str], self.request.app.get("_base64_key"))

        if update.is_testable:
            return None

        if not base64_key:
            logger.warning(
                "Validation was skipped because there is no base64 key to compare hash",
                UserWarning,
                stacklevel=2,
            )
            return None

        try:
            update.verify_signature(base64_key)
        except WebhookSignatureUnverified:
            logger.debug(
                "Request has being blocked due to invalid signature of json request payload."
            )
            raise web.HTTPBadRequest()

    def ok_response(self) -> web.Response:
        return web.Response(text="ok")

    app_key_check_ip = "_qiwi_wallet_check_ip"
    app_key_dispatcher = "_qiwi_wallet_dispatcher"
