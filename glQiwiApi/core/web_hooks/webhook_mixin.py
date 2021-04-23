import asyncio
import logging
from typing import Optional, Any

from aiohttp import web
from aiohttp.abc import AbstractAccessLogger

from glQiwiApi.core.web_hooks import handler, server


class AccessLogger(AbstractAccessLogger):
    """ Custom logger for aiohttp.web.Application """

    def log(self, request, response, time) -> None:
        self.logger.info(f'{request.remote} '
                         f'"{request.method} {request.path} '
                         f'done in {time}s: {response.status}')


class HookMixin:
    """
    Mixin, which includes webhook poling methods

    """
    handler_manager: Optional[handler.HandlerManager] = None
    """handler_manager class. sooner will be bind if needed"""

    def __init__(self) -> None:
        self.handler_manager = handler.HandlerManager(
            loop=asyncio.get_event_loop()
        )

    def start_polling(
            self,
            host: str = "localhost",
            port: int = 8080,
            path: Optional[str] = None,
            app: Optional["web.Application"] = None,
            access_logger: Optional[AbstractAccessLogger] = None,
            **logger_config: Any
    ):
        """
        Blocking function, which listen webhooks

        :param host: server host
        :param port: server port that open for tcp/ip trans.
        :param path: path for qiwi that will send requests
        :param app: pass web.Application
        :param access_logger: pass heir of AbstractAccessLogger,
         if you want custom logger
        """
        from aiohttp import web

        app = app if app is not None else web.Application()

        server.setup(self.handler_manager, app, path)

        logging.basicConfig(**logger_config)

        if not isinstance(access_logger, AbstractAccessLogger):
            access_logger = AccessLogger

        web.run_app(
            app,
            host=host,
            port=port,
            access_log_class=access_logger
        )

    @property
    def transaction_handler(self) -> handler.HandlerManager:
        """
        Handler manager for default qiwi transactions,
        you can pass on lambda filter, if you want
        But it must to return bool

        """
        return self.handler_manager

    @property
    def bill_handler(self) -> handler.HandlerManager:
        """
        Handler manager for p2p bills,
        you can pass on lambda filter, if you want
        But it must to return bool
        """
        return self.handler_manager
