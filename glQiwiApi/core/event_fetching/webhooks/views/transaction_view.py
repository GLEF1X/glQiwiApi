import logging

from aiohttp import web


from glQiwiApi.core.event_fetching.webhooks.dto.errors import WebhookAPIError
from glQiwiApi.core.event_fetching.webhooks.views.base import BaseWebhookView
from glQiwiApi.qiwi.clients.wallet.types.webhooks import TransactionWebhook
from glQiwiApi.types.exceptions import WebhookSignatureUnverifiedError

logger = logging.getLogger("glQiwiApi.webhooks.transaction")


class QiwiTransactionWebhookView(BaseWebhookView[TransactionWebhook]):
    def _validate_event_signature(self, update: TransactionWebhook) -> None:
        if update.is_experimental:  # pragma: no cover
            return None

        logger.debug("Current encryption key is %s", self._encryption_key)

        try:
            update.verify_signature(self._encryption_key)
        except WebhookSignatureUnverifiedError:
            logger.debug(
                "Request has being blocked due to invalid signature of json request payload."
            )
            raise web.HTTPBadRequest(
                text=WebhookAPIError(status="Invalid hash of transaction.").json(),
                content_type="application/json",
            )

    async def ok_response(self) -> web.Response:
        return web.Response(text="ok")
