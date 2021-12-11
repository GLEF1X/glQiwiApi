import logging

from aiohttp import web

from glQiwiApi import types
from glQiwiApi.core.dispatcher.webhooks.dto.errors import WebhookAPIError
from glQiwiApi.core.dispatcher.webhooks.views.base import BaseWebhookView
from glQiwiApi.types.exceptions import WebhookSignatureUnverified

logger = logging.getLogger("glQiwiApi.webhooks.transaction")


class QiwiTransactionWebhookView(BaseWebhookView[types.TransactionWebhook]):
    def _validate_event_signature(self, update: types.TransactionWebhook) -> None:
        if update.is_experimental:  # pragma: no cover
            return None

        try:
            update.verify_signature(self._encryption_key)
        except WebhookSignatureUnverified:
            logger.debug(
                "Request has being blocked due to invalid signature of json request payload."
            )
            raise web.HTTPBadRequest(
                body=WebhookAPIError(status="Invalid hash of transaction.").json(),
                content_type="application/json"
            )

    async def ok_response(self) -> web.Response:
        return web.Response(text="ok")
