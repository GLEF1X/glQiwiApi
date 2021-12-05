from __future__ import annotations

import typing as t
from ssl import SSLContext

from aiohttp import web

from glQiwiApi.plugins.telegram.base import TelegramPlugin

if t.TYPE_CHECKING:
    from glQiwiApi.utils.compat import Dispatcher

# Some aliases =)
ListOfRoutes = t.List[web.ResourceRoute]
SubApps = t.List[t.Tuple[str, web.Application, ListOfRoutes]]


def _init_sub_apps_handlers(app: web.Application, routes: ListOfRoutes) -> None:
    """
    Initialize sub application handlers

    :param app:
    :param routes: list of AbstractRoute subclasses
    """
    for route in routes:  # pragma: no cover
        app.router.add_route(
            handler=route.handler,
            method=route.method,
            name=route.name,
            path=route.url_for().path,
        )


class TelegramWebhookPlugin(TelegramPlugin):
    """
    Managing loading webhooks of aiogram together with QiwiWrapper

    """

    execution_path: str = "/bot/{token}"
    """You can override this parameter to change the default route path"""

    prefix: str = "/tg/webhooks"
    """ You can override the prefix for the application """

    def __init__(
            self,
            dispatcher: Dispatcher,
            ssl_certificate: SSLContext,
            webhook_domain: str,
            route_name: str = "webhook_handler",
            sub_apps: t.Optional[SubApps] = None
    ) -> None:
        """

        :param dispatcher: instance of aiogram class Dispatcher
        :param ssl_certificate: self-signed or default ssl certificate
        :param webhook_domain: your domain such like https://example.com
        :param route_name: name of aiogram webhook router
        :param sub_apps: list of tuples(prefix as string, web.Application)
        """
        from aiogram.dispatcher.webhook import WebhookRequestHandler

        super(TelegramWebhookPlugin, self).__init__(dispatcher)
        self._app: web.Application = web.Application()
        self._app.router.add_route(
            "*", self.execution_path, WebhookRequestHandler, name=route_name
        )
        self._app["BOT_DISPATCHER"] = self.dispatcher
        self.sub_apps: SubApps = sub_apps or []
        self._ssl_context = ssl_certificate
        self._webhook_domain = webhook_domain

    async def incline(self, ctx: t.Dict[t.Any, t.Any]) -> web.Application:
        """
        A method that connects the main application, and the proxy in the form of a telegram

        :param ctx: keyword arguments, which contains application and host
        """
        main_app = t.cast(web.Application, ctx.get("app"))
        main_app.add_subapp(self.prefix, self._app)
        for prefix, sub_app, handlers in self.sub_apps:
            sub_app["bot"] = self.bot
            sub_app["dp"] = self.dispatcher
            _init_sub_apps_handlers(sub_app, handlers)
            main_app.add_subapp(prefix, sub_app)
        await self.configure_webhook(ctx)

        return self._app

    async def configure_webhook(self, ctx: t.Dict[t.Any, t.Any]) -> None:
        """
        You can override this method to correctly setup webhooks with aiogram
        API method `set_webhook` like this: self.dispatcher.bot.set_webhook()

        """
        full_url = self._webhook_domain + self.prefix
        if isinstance(self.execution_path, str):
            full_url += self.execution_path
        await self.dispatcher.bot.set_webhook(full_url, certificate=self._ssl_context, **ctx)

    async def shutdown(self) -> None:
        await self.dispatcher.storage.close()
        await self.dispatcher.storage.wait_closed()
        await self.dispatcher.bot.session.close()
