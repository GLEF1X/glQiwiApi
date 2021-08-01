from __future__ import annotations

import warnings

from aiohttp import web
from pydantic import ValidationError

from glQiwiApi import types
from glQiwiApi.core.dispatcher.webhooks.base import BaseWebHookView
from glQiwiApi.core.dispatcher.webhooks.utils import check_ip
from glQiwiApi.utils.api_helper import hmac_for_transaction


class QiwiWalletWebView(BaseWebHookView[types.WebHook]):
    """
    View, which processes transactions

    """

    def _check_ip(self, ip_address: str) -> bool:
        return check_ip(ip_address)

    async def parse_update(self) -> types.WebHook:
        """Parse raw update and return pydantic model"""
        data = await self.request.json()
        try:
            return types.WebHook.parse_raw(data)
        except ValidationError as ex:
            raise web.HTTPBadRequest(text=ex.json())

    def _hash_validator(self, update: types.WebHook) -> None:
        base64_key = self.request.app.get("_base64_key")

        if not update.payment:
            return
        if not base64_key:
            warnings.warn(
                "Validation was skipped because there is no base64 key to compare hash",
                UserWarning,
                stacklevel=2
            )
            return

        validated = hmac_for_transaction(
            webhook_key_base64=base64_key,
            amount=update.payment.sum,
            txn_hash=update.hash,
            txn_type=update.payment.type,
            txn_id=update.payment.txn_id,
            account=update.payment.account,
        )

        if not validated:
            raise web.HTTPBadRequest()

    app_key_check_ip = "_qiwi_wallet_check_ip"
    app_key_handler_manager = "_qiwi_wallet_handler_manager"
