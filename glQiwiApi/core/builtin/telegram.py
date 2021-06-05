from __future__ import annotations

import abc
import typing
from asyncio import AbstractEventLoop

from aiohttp import web

from glQiwiApi.utils.basics import take_event_loop

if typing.TYPE_CHECKING:
    try:
        from aiogram import Dispatcher
    except (ModuleNotFoundError, ImportError):
        pass

__all__ = ["TelegramWebhookProxy", "TelegramPollingProxy", "BaseProxy"]

# Some aliases =)
ListOfRoutes = typing.List[web.ResourceRoute]
SubApps = typing.List[typing.Tuple[str, web.Application, ListOfRoutes]]


def _init_sub_apps_handlers(app: web.Application, routes: ListOfRoutes):
    """
    Initialize sub application handlers

    :param app:
    :param routes: list of AbstractRoute subclasses
    """
    for route in routes:
        app.router.add_route(
            handler=route.handler,
            method=route.method,
            name=route.name,
            path=route.url_for().path
        )


class BaseProxy(abc.ABC):

    def __init__(self, dispatcher: Dispatcher, *,
                 loop: typing.Optional[AbstractEventLoop] = None):
        self.bot = dispatcher.bot
        self.dispatcher = dispatcher

        if isinstance(loop, AbstractEventLoop):
            if loop.is_closed():
                raise RuntimeError("The event loop, that you have passed on is closed")
            self._loop = loop
        else:
            self._loop = take_event_loop(set_debug=True)

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

    def __init__(self, dispatcher: Dispatcher, sub_apps: typing.Optional[SubApps] = None):
        """

        :param dispatcher: instance of aiogram class Dispatcher
        :param sub_apps: list of tuples(prefix as string, web.Application)
        """
        from aiogram.dispatcher.webhook import WebhookRequestHandler

        super(TelegramWebhookProxy, self).__init__(dispatcher)
        self._app: web.Application = web.Application()
        self._app.router.add_route(
            '*', self.execution_path, WebhookRequestHandler,
            name='webhook_handler'
        )
        self._app['BOT_DISPATCHER'] = self.dispatcher
        self.sub_apps: SubApps = sub_apps or []

    def setup(self, **kwargs) -> web.Application:
        """
        A method that connects the main application, and the proxy in the form of a telegram

        :param kwargs: keyword arguments, which contains application and host
        """
        main_app: web.Application = kwargs.pop("app")
        host: str = kwargs.pop("host")

        main_app.add_subapp(self.prefix, self._app)
        for prefix, sub_app, handlers in self.sub_apps:
            sub_app['bot'] = self.bot
            sub_app['dp'] = self.dispatcher
            _init_sub_apps_handlers(sub_app, handlers)
            main_app.add_subapp(prefix, sub_app)
        self._loop.run_until_complete(
            self.configure_webhook(host, **kwargs)
        )

        return self._app

    async def configure_webhook(self, host: str, **kwargs) -> typing.Any:
        """
        You can override this method to correctly setup webhooks with aiogram
        API method `set_webhook` like this: self.dispatcher.bot.set_webhook()

        """

        full_url: str = host + self.prefix

        if isinstance(self.execution_path, str):
            full_url += self.execution_path

        await self.dispatcher.bot.set_webhook(full_url, **kwargs)


class TelegramPollingProxy(BaseProxy):
    """
    Builtin telegram proxy.
    Allows you to use Telegram and QIWI webhooks together

    """

    def setup(self, **kwargs: typing.Any):
        """
        Set up polling to run polling qiwi updates concurrently with aiogram

        :param kwargs: you can pass on loop as key/value parameter
        """
        loop = kwargs.pop("loop") or self._loop
        loop.create_task(self.dispatcher.start_polling(**kwargs))
