from __future__ import annotations

import typing as t

from glQiwiApi.plugins.telegram.base import TelegramPlugin

if t.TYPE_CHECKING:
    from glQiwiApi.utils.compat import Dispatcher


class TelegramPollingPlugin(TelegramPlugin):
    """
    Builtin telegram proxy.
    Allows you to use Telegram and QIWI webhooks together

    """

    def __init__(
            self,
            dispatcher: Dispatcher,
            timeout: int = 20,
            relax: float = 0.1,
            limit: t.Optional[t.Any] = None,
            reset_webhook: t.Optional[t.Any] = None,
            fast: t.Optional[bool] = True,
            error_sleep: int = 5,
            allowed_updates: t.Optional[t.List[str]] = None,
    ) -> None:
        super(TelegramPollingPlugin, self).__init__(dispatcher)
        self._allowed_updates = allowed_updates
        self._error_sleep = error_sleep
        self._fast = fast
        self._reset_webhook = reset_webhook
        self._timeout = timeout
        self._relax = relax
        self._limit = limit

    async def incline(self, ctx: t.Dict[t.Any, t.Any]) -> t.Any:
        """
        Set up polling to run polling qiwi updates concurrently with aiogram

        :param ctx: you can pass on loop as key/value parameter
        """
        await self.dispatcher.start_polling(
            timeout=self._timeout,
            reset_webhook=self._reset_webhook,
            relax=self._relax,
            allowed_updates=self._allowed_updates,
            limit=self._limit,
            error_sleep=self._error_sleep,
            fast=self._fast,
        )

    async def shutdown(self) -> None:
        self.dispatcher.stop_polling()
