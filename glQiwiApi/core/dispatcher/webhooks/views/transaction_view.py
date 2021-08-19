from __future__ import annotations

import warnings
from typing import cast, Optional

from aiohttp import web
from pydantic import ValidationError

from glQiwiApi import types
from glQiwiApi.core.dispatcher.webhooks.base import BaseWebHookView
from glQiwiApi.utils.errors import WebhookSignatureUnverified

try:
    import orjson as json
except ImportError:
    import json  # type: ignore


class QiwiWebHookWebView(BaseWebHookView[types.WebHook]):
    """
    View, which processes transactions

    """

    async def parse_update(self) -> types.WebHook:
        """Parse raw update and return pydantic model"""
        data = await self.request.json(loads=json.loads)
        try:
            return types.WebHook.parse_raw(data)
        except ValidationError:
            raise web.HTTPBadRequest()

    def _validate_event_signature(self, update: types.WebHook) -> None:
        base64_key = cast(Optional[str], self.request.app.get("_base64_key"))

        if not update.payment:
            return None

        if not base64_key:
            warnings.warn(
                "Validation was skipped because there is no base64 key to compare hash",
                UserWarning,
                stacklevel=2,
            )
            return None

        try:
            update.verify_signature(base64_key)
        except WebhookSignatureUnverified:
            self.dispatcher.logger.warning(
                "Blocking request due to invalid signature of json request payload."
            )
            raise web.HTTPBadRequest()

    def ok_response(self) -> web.Response:
        return web.Response(text="ok")

    app_key_check_ip = "_qiwi_wallet_check_ip"
    app_key_dispatcher = "_qiwi_wallet_dispatcher"
