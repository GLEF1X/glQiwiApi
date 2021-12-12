from __future__ import annotations

import typing as t

from aiohttp import web
from aiohttp.web import _run_app

from glQiwiApi.core.dispatcher.webhooks.config import ApplicationConfig
from glQiwiApi.plugins import Pluggable

if t.TYPE_CHECKING:
    from glQiwiApi.utils.compat import Dispatcher

# Some aliases =)
ListOfRoutes = t.List[web.ResourceRoute]
SubApps = t.List[t.Tuple[str, web.Application, ListOfRoutes]]


class TelegramWebhookPlugin(Pluggable):
    """
    Managing loading webhooks of aiogram together with QiwiWrapper

    """

    def __init__(
            self,
            dispatcher: Dispatcher,
            host: str,
            path: str = "/bot/{token}",
            prefix: str = "/tg/webhooks",
            route_name: str = "webhook_handler",
            app_config: ApplicationConfig = ApplicationConfig(),
            **kwargs: t.Any
    ) -> None:
        """

        :param dispatcher: instance of aiogram class Dispatcher
        :param route_name: name of aiogram webhook router
        :param sub_apps: list of tuples(prefix as string, web.Application)
        """
        from aiogram.dispatcher.webhook import WebhookRequestHandler

        self._path = path.format(token=dispatcher.bot._token)
        self._prefix = prefix
        self._host = host
        self._dispatcher = dispatcher
        self._app = web.Application()
        self._app_config = app_config

        self._app.router.add_route(
            "*", self._path, WebhookRequestHandler, name=route_name
        )
        self._app["BOT_DISPATCHER"] = self._dispatcher

        self._set_webhook_kwargs = kwargs

    async def install(self, ctx: t.Dict[t.Any, t.Any]) -> None:
        """
        A method that connects the main application, and the proxy in the form of a telegram

        :param ctx: keyword arguments, which contains application and host
        """
        await self._set_telegram_webhook(ctx)
        await _run_app(self._app, host=self._app_config.host, port=self._app_config.port,
                       ssl_context=self._app_config.ssl_certificate.as_ssl_context())

    async def _set_telegram_webhook(self, ctx: t.Dict[t.Any, t.Any]) -> None:
        """
        You can override this method to correctly setup webhooks with aiogram
        API method `_set_telegram_webhook` like this: self.dispatcher.bot._set_telegram_webhook()

        """
        url = self._host + self._prefix + self._path
        await self._dispatcher.bot.set_webhook(
            url=url,
            # TODO check if `ssl_certificate` is None
            certificate=self._app_config.ssl_certificate.as_input_file(),
            **self._set_webhook_kwargs
        )

    async def shutdown(self) -> None:
        await self._dispatcher.storage.close()
        await self._dispatcher.storage.wait_closed()
        await self._dispatcher.bot.session.close()
