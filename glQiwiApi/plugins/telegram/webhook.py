from __future__ import annotations

import typing as t

from aiohttp import web

from glQiwiApi.plugins.telegram.base import TelegramPlugin
from glQiwiApi.utils.certificates import SSLCertificate

if t.TYPE_CHECKING:
    from glQiwiApi.utils.compat import Dispatcher

# Some aliases =)
ListOfRoutes = t.List[web.ResourceRoute]
SubApps = t.List[t.Tuple[str, web.Application, ListOfRoutes]]


class TelegramWebhookPlugin(TelegramPlugin):
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
            **kwargs
    ) -> None:
        """

        :param dispatcher: instance of aiogram class Dispatcher
        :param route_name: name of aiogram webhook router
        :param sub_apps: list of tuples(prefix as string, web.Application)
        """
        from aiogram.dispatcher.webhook import WebhookRequestHandler

        super(TelegramWebhookPlugin, self).__init__(dispatcher)
        self._path = path.format(token=dispatcher.bot._token)
        self._prefix = prefix
        self._host = host
        self._app: web.Application = web.Application()
        self._app.router.add_route(
            "*", self._path, WebhookRequestHandler, name=route_name
        )
        self._app["BOT_DISPATCHER"] = self.dispatcher
        self._set_webhook_kwargs = kwargs

    async def incline(self, ctx: t.Dict[t.Any, t.Any]) -> web.Application:
        """
        A method that connects the main application, and the proxy in the form of a telegram

        :param ctx: keyword arguments, which contains application and host
        """
        main_app = t.cast(web.Application, ctx.get("app"))
        main_app.add_subapp(self._prefix, self._app)
        await self._set_webhook(ctx)
        return self._app

    async def _set_webhook(self, ctx: t.Dict[t.Any, t.Any]) -> None:
        """
        You can override this method to correctly setup webhooks with aiogram
        API method `_set_webhook` like this: self.dispatcher.bot._set_webhook()

        """
        certificate: SSLCertificate = ctx.pop("certificate")
        url = self._host + self._prefix + self._path
        await self.dispatcher.bot.set_webhook(
            url=url,
            certificate=certificate.as_input_file(),
            **self._set_webhook_kwargs
        )

    async def shutdown(self) -> None:
        await self.dispatcher.storage.close()
        await self.dispatcher.storage.wait_closed()
        await self.dispatcher.bot.session.close()
