from __future__ import annotations

import typing as t

from aiohttp import web
from aiohttp.web import _run_app

from glQiwiApi.core.event_fetching.webhooks.config import ApplicationConfig
from glQiwiApi.plugins import Pluggable

if t.TYPE_CHECKING:
    from glQiwiApi.utils.compat import Dispatcher

ListOfRoutes = t.List[web.ResourceRoute]
SubApps = t.List[t.Tuple[str, web.Application, ListOfRoutes]]

DEFAULT_TELEGRAM_WEBHOOK_PATH_PREFIX = '/tg/webhooks'
DEFAULT_TELEGRAM_WEBHOOK_PATH = '/bot/{token}'
DEFAULT_TELEGRAM_WEBHOOK_ROUTE_NAME = 'webhook_handler'

# This one was created only for testing purposes
run_app = _run_app


class SSLCertificateIsMissingError(Exception):
    pass


class AiogramWebhookPlugin(Pluggable):
    """
    Managing loading webhooks of aiogram together with QiwiWrapper

    """

    def __init__(
        self,
        dispatcher: Dispatcher,
        host: str,
        path: str = DEFAULT_TELEGRAM_WEBHOOK_PATH,
        prefix: str = DEFAULT_TELEGRAM_WEBHOOK_PATH_PREFIX,
        route_name: str = DEFAULT_TELEGRAM_WEBHOOK_ROUTE_NAME,
        app_config: ApplicationConfig = ApplicationConfig(),
        **kwargs: t.Any,
    ) -> None:
        """

        :param dispatcher: instance of aiogram class Dispatcher
        :param route_name: name of aiogram webhook router
        :param sub_apps: list of tuples(prefix as string, web.Application)
        """
        from aiogram.dispatcher.webhook import WebhookRequestHandler

        self._path = prefix + path.format(token=dispatcher.bot._token)
        self._host = host
        self._dispatcher = dispatcher
        self._prefix = prefix

        self._app = web.Application()
        self._app_config = app_config
        self._app.router.add_route('*', self._path, WebhookRequestHandler, name=route_name)
        self._app['BOT_DISPATCHER'] = self._dispatcher
        self._set_webhook_kwargs = kwargs

        if self._app_config.ssl_certificate is None:
            raise SSLCertificateIsMissingError(
                "Webhooks won't work without ssl_certificate. "
                'To fix it, please transmit ssl_certificate to ApplicationConfig to TelegramWebhookPlugin'
            )

    async def install(self, ctx: t.Dict[t.Any, t.Any]) -> None:
        """
        A method that connects the main application, and the proxy in the form of a telegram

        :param ctx: keyword arguments, which contains application and host
        """
        await self._set_telegram_webhook(ctx)
        await run_app(
            self._app,
            host=self._app_config.host,
            port=self._app_config.port,
            ssl_context=self._app_config.ssl_certificate.as_ssl_context(),  # type: ignore
        )

    async def _set_telegram_webhook(self, ctx: t.Dict[t.Any, t.Any]) -> None:
        """
        You can override this method to correctly setup webhooks with aiogram
        self.dispatcher.bot.set_webhook(...)

        """
        url = self._host + self._path
        await self._dispatcher.bot.set_webhook(
            url=url,
            certificate=self._app_config.ssl_certificate.as_input_file(),  # type: ignore
            **self._set_webhook_kwargs,
        )

    async def shutdown(self) -> None:
        await self._dispatcher.storage.close()
        await self._dispatcher.storage.wait_closed()
        await self._dispatcher.bot.session.close()
