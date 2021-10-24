from __future__ import annotations

import abc
import typing
from asyncio import AbstractEventLoop, get_event_loop
from ssl import SSLContext

from aiohttp import web

if typing.TYPE_CHECKING:
    from glQiwiApi.utils.compat import Dispatcher

__all__ = ["TelegramWebhookProxy", "TelegramPollingProxy", "BaseProxy"]

# Some aliases =)
ListOfRoutes = typing.List[web.ResourceRoute]
SubApps = typing.List[typing.Tuple[str, web.Application, ListOfRoutes]]


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


class BaseProxy(abc.ABC):
    def __init__(
            self, dispatcher: Dispatcher, *, loop: typing.Optional[AbstractEventLoop] = None
    ) -> None:
        self.bot = dispatcher.bot
        self.dispatcher = dispatcher
        if loop is not None:
            self._loop = loop
        else:
            self._loop = get_event_loop()

    @abc.abstractmethod
    def setup(self, **kwargs: typing.Any) -> typing.Any:
        """
        This method should establish the necessary for work

        """
        raise NotImplementedError


class TelegramWebhookProxy(BaseProxy):
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
            sub_apps: typing.Optional[SubApps] = None,
            loop: typing.Optional[AbstractEventLoop] = None,
    ) -> None:
        """

        :param dispatcher: instance of aiogram class Dispatcher
        :param ssl_certificate: self-signed or default ssl certificate
        :param webhook_domain: your domain such like https://example.com
        :param route_name: name of aiogram webhook router
        :param sub_apps: list of tuples(prefix as string, web.Application)
        """
        from aiogram.dispatcher.webhook import WebhookRequestHandler

        super(TelegramWebhookProxy, self).__init__(dispatcher, loop=loop)
        self._app: web.Application = web.Application()
        self._app.router.add_route(
            "*", self.execution_path, WebhookRequestHandler, name=route_name
        )
        self._app["BOT_DISPATCHER"] = self.dispatcher
        self.sub_apps: SubApps = sub_apps or []
        self._ssl_context = ssl_certificate
        self._webhook_domain = webhook_domain

    @property
    def ssl_context(self) -> SSLContext:
        return self._ssl_context

    def setup(self, **kwargs: typing.Any) -> web.Application:
        """
        A method that connects the main application, and the proxy in the form of a telegram

        :param kwargs: keyword arguments, which contains application and host
        """
        main_app: web.Application = kwargs.pop("app")

        main_app.add_subapp(self.prefix, self._app)
        # print(main_app.router.routes())
        for prefix, sub_app, handlers in self.sub_apps:
            sub_app["bot"] = self.bot
            sub_app["dp"] = self.dispatcher
            _init_sub_apps_handlers(sub_app, handlers)
            main_app.add_subapp(prefix, sub_app)
        self._loop.run_until_complete(self.configure_webhook(**kwargs))

        return self._app

    async def configure_webhook(self, **kwargs: typing.Any) -> None:
        """
        You can override this method to correctly setup webhooks with aiogram
        API method `set_webhook` like this: self.dispatcher.bot.set_webhook()

        """
        full_url = self._webhook_domain + self.prefix
        if isinstance(self.execution_path, str):
            full_url += self.execution_path
        await self.dispatcher.bot.set_webhook(
            full_url, certificate=self._ssl_context, **kwargs
        )


class TelegramPollingProxy(BaseProxy):
    """
    Builtin telegram proxy.
    Allows you to use Telegram and QIWI webhooks together

    """

    def __init__(
            self,
            dispatcher: Dispatcher,
            loop: typing.Optional[AbstractEventLoop] = None,
            timeout: int = 20,
            relax: float = 0.1,
            limit: typing.Optional[typing.Any] = None,
            reset_webhook: typing.Optional[typing.Any] = None,
            fast: typing.Optional[bool] = True,
            error_sleep: int = 5,
            allowed_updates: typing.Optional[typing.List[str]] = None,
    ) -> None:
        super(TelegramPollingProxy, self).__init__(dispatcher, loop=loop)
        self._allowed_updates = allowed_updates
        self._error_sleep = error_sleep
        self._fast = fast
        self._reset_webhook = reset_webhook
        self._timeout = timeout
        self._relax = relax
        self._limit = limit

    def setup(self, **kwargs: typing.Any) -> None:
        """
        Set up polling to run polling qiwi updates concurrently with aiogram

        :param kwargs: you can pass on loop as key/value parameter
        """
        loop = kwargs.pop("loop") or self._loop  # pragma: no cover
        loop.create_task(  # pragma: no cover
            self.dispatcher.start_polling(
                timeout=self._timeout,
                reset_webhook=self._reset_webhook,
                relax=self._relax,
                allowed_updates=self._allowed_updates,
                limit=self._limit,
                error_sleep=self._error_sleep,
                fast=self._fast,
            )
        )
