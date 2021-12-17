import logging
from typing import cast

from aiohttp import web

from glQiwiApi import types
from glQiwiApi.core.dispatcher.webhooks.views.base import BaseWebhookView
from glQiwiApi.types.exceptions import WebhookSignatureUnverifiedError

logger = logging.getLogger("glQiwiApi.webhooks.p2p")


class QiwiBillWebhookView(BaseWebhookView[types.BillWebhook]):
    """View, which processes p2p notifications"""

    def _validate_event_signature(self, update: types.BillWebhook) -> None:
        sha256_signature = cast(
            str, self.request.headers.get("X-Api-Signature-SHA256")
        )  # pragma: no cover

        try:  # pragma: no cover
            update.verify_signature(sha256_signature, self._encryption_key)  # pragma: no cover
        except WebhookSignatureUnverifiedError:  # pragma: no cover
            logger.debug(
                "Blocking request due to invalid signature of payload."
            )  # pragma: no cover
            raise web.HTTPBadRequest()  # pragma: no cover

    async def ok_response(self) -> web.Response:
        return web.json_response(data={"error": "0"})
