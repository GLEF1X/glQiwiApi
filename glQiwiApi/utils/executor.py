"""
Managing polling and webhooks
"""
from __future__ import annotations

import asyncio
import inspect
import logging
import types
from datetime import datetime, timedelta
from ssl import SSLContext
from typing import (
    Union,
    Optional,
    List,
    Callable,
    Awaitable,
    TypeVar,
    TYPE_CHECKING,
    Any,
    cast,
    NoReturn,
)

from aiohttp import ClientTimeout, web

from glQiwiApi.core.builtin import BaseProxy, logger, TelegramWebhookProxy
from glQiwiApi.core.constants import DEFAULT_TIMEOUT
from glQiwiApi.core.dispatcher.webhooks import server
from glQiwiApi.core.dispatcher.webhooks.config import Path
from glQiwiApi.core.synchronous.decorator import run_forever_safe
from glQiwiApi.types import Transaction
from glQiwiApi.utils.errors import NoUpdatesToExecute

__all__ = ["start_webhook", "start_polling"]

if TYPE_CHECKING:
    from glQiwiApi.qiwi.client import QiwiWrapper  # pragma: no cover


class BadCallback(Exception):
    ...


T = TypeVar("T")


def start_webhook(
        client: QiwiWrapper,
        *,
        host: str = "localhost",
        port: int = 8080,
        path: Optional[Path] = None,
        on_startup: Optional[Callable[[QiwiWrapper], Awaitable[None]]] = None,
        on_shutdown: Optional[Callable[[QiwiWrapper], Awaitable[None]]] = None,
        tg_app: Optional[TelegramWebhookProxy] = None,
        app: Optional["web.Application"] = None,
        ssl_context: Optional[SSLContext] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
) -> None:
    """
    Blocking function that listens for webhooks

    :param client: instance of QiwiWrapper
    :param host: server host
    :param port: server port that open for tcp/ip trans.
    :param path: path for qiwi that will send requests
    :param app: pass web.Application
    :param on_startup: coroutine,which will be executed on startup
    :param on_shutdown: coroutine, which will be executed on shutdown
    :param tg_app: builtin TelegramWebhookProxy or other
          or class, that inherits from BaseProxy and deal with aiogram updates
    :param ssl_context:
    :param loop:
    """
    executor = Executor(client, tg_app=tg_app, loop=loop)
    _setup_callbacks(executor, on_startup, on_shutdown)
    if isinstance(tg_app, TelegramWebhookProxy) and ssl_context is None:
        ssl_context = tg_app.ssl_context
    executor.start_webhook(host=host, port=port, path=path, app=app, ssl_context=ssl_context)


def start_polling(
        client: QiwiWrapper,
        *,
        get_updates_from: Optional[datetime] = None,
        timeout: Union[float, int, ClientTimeout] = 5,
        on_startup: Optional[Callable[[QiwiWrapper], Any]] = None,
        on_shutdown: Optional[Callable[[QiwiWrapper], Any]] = None,
        tg_app: Optional[BaseProxy] = None,
) -> None:
    """
    Setup for long-polling mode

    :param client: instance of QiwiWrapper
    :param get_updates_from: date from which will be polling,
         if it's None, polling will skip all updates
    :param timeout: timeout of polling in seconds, if the timeout is too small,
         the API can throw an exception
    :param on_startup: function or coroutine,
         which will be executed on startup
    :param on_shutdown: function or coroutine,
         which will be executed on shutdown
    :param tg_app: builtin TelegramPollingProxy or other
         class, that inherits from BaseProxy, deal with aiogram updates
    """
    executor = Executor(client, tg_app=tg_app)
    _setup_callbacks(executor, on_startup, on_shutdown)
    executor.start_polling(get_updates_from=get_updates_from, timeout=timeout)


async def _inspect_and_execute_callback(
        client: "QiwiWrapper", callback: Callable[[QiwiWrapper], Any]
) -> None:
    if inspect.iscoroutinefunction(callback):
        await callback(client)
    else:
        callback(client)  # pragma: no cover


def _check_callback(callback: Callable[[QiwiWrapper], Any]) -> NoReturn:
    if not isinstance(callback, types.FunctionType):
        raise BadCallback("Callback passed to on_startup / on_shutdown is not a function")  # NOQA  # pragma: no cover


def _setup_callbacks(
        executor: Executor,
        on_startup: Optional[Callable[[QiwiWrapper], Any]] = None,
        on_shutdown: Optional[Callable[[QiwiWrapper], Any]] = None,
) -> None:
    """
    Function, which setup callbacks and set it to dispatcher object

    :param executor:
    :param on_startup:
    :param on_shutdown:
    """
    if on_startup is not None:
        executor.add_startup_callback(on_startup)
    if on_shutdown is not None:
        executor.add_shutdown_callback(on_shutdown)  # pragma: no cover


def parse_timeout(timeout: Union[float, int, ClientTimeout]) -> float:  # pragma: no cover
    if isinstance(timeout, float):
        return timeout
    elif isinstance(timeout, int):
        return float(timeout)
    elif isinstance(timeout, ClientTimeout):
        return timeout.total or DEFAULT_TIMEOUT.total  # type: ignore
    else:
        raise TypeError(
            "Timeout must be float, int or ClientTimeout. You have "
            f"passed on {type(timeout)}"
        )


class Executor:
    def __init__(
            self,
            client: QiwiWrapper,
            tg_app: Optional[BaseProxy],
            loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """

        :param client: instance of BaseWrapper
        :param tg_app: optional proxy to connect aiogram polling/webhook mode
        """
        if loop is not None:
            self._loop = loop  # pragma: no cover

        self.dispatcher = client.dp
        self._logger_config = {
            "handlers": [logger.InterceptHandler()],
            "level": logging.DEBUG,
        }
        self._tg_app = tg_app
        self.offset: Optional[int] = None
        self.get_updates_until: Optional[datetime] = None
        self.get_updates_from: Optional[datetime] = None
        self.client: QiwiWrapper = client
        self._on_startup_calls: List[Callable[..., Any]] = []
        self._on_shutdown_calls: List[Callable[..., Any]] = []
        self._timeout: Optional[float] = None

    @property
    def telegram_proxy_application(self) -> Optional[BaseProxy]:
        return self._tg_app

    def _create_new_loop_if_closed(self) -> None:
        if self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        self._loop = cast(asyncio.AbstractEventLoop, getattr(self, "_loop", asyncio.get_event_loop()))
        # There is a issue, connected with aiohttp.web application, because glQiwiApi wants to have the same interface
        # for polling and webhooks on_startup & on_shutdown callbacks,
        # so we don't use app.on_shutdown.append(...), on the contrary we use self-written
        # system of callbacks, and so aiohttp.web.Application close event loop on shutdown, that's why we need to
        # create new event loop to gracefully execute shutdown callback.
        # It is highly undesirable to delete this line because you will always catch RuntimeWarning and RuntimeError.
        self._create_new_loop_if_closed()
        return self._loop

    def add_shutdown_callback(self, callback: Callable[[QiwiWrapper], Any]) -> None:
        _check_callback(callback)
        self._on_shutdown_calls.append(callback)

    def add_startup_callback(self, callback: Callable[[QiwiWrapper], Any]) -> None:
        _check_callback(callback)
        self._on_startup_calls.append(callback)

    async def _prepare_date_boundaries(self, get_updates_from: Optional[datetime]) -> None:
        """
        Preprocess method, which set start date and end date of polling

        :param get_updates_from: date from which will be polling
        """
        current_time = datetime.now()
        if get_updates_from is None:
            get_updates_from = current_time - timedelta(seconds=self._timeout)  # type: ignore
        self.get_updates_from = get_updates_from
        self.get_updates_until = current_time

    async def _fetch_updates(self) -> List[Transaction]:
        history = await self.client.transactions(end_date=self.get_updates_until, start_date=self.get_updates_from)
        if not history:
            raise NoUpdatesToExecute()
        return history

    async def _pool_process(self, get_updates_from: Optional[datetime]) -> None:
        """
        Method, which manage pool process

        :param get_updates_from: date from which will be polling
        """
        await self._prepare_date_boundaries(get_updates_from)
        try:
            # Here we get transactions from old to new like [3, 2, 1](a list of mock id's of events)
            history_from_last_to_first: List[Transaction] = await self._fetch_updates()
        except NoUpdatesToExecute:
            return
        # Convert it to list of transactions with id's like [1, 2, 3] and work with it
        history_from_first_to_last: List[Transaction] = history_from_last_to_first[::-1]

        if self.offset is None:
            first_payment: Transaction = history_from_first_to_last[0]
            self.offset = first_payment.id - 1

        await self.process_events(history_from_first_to_last)

    async def _start_polling(self, **kwargs: Any) -> None:
        """Blocking method, which start polling process"""
        self._timeout = timeout_to_sleep = parse_timeout(kwargs.pop("timeout"))
        while True:
            try:
                await self._pool_process(**kwargs)
            except Exception as ex:
                self.dispatcher.logger.error(
                    "Handle `%s`. Sleeping %s seconds", repr(ex), self._timeout + 100
                )
            await asyncio.sleep(timeout_to_sleep)

    def _on_shutdown(self) -> None:
        """
        On shutdown, executor gracefully cancel all tasks, close event loop
        and call `close` method to clear resources
        """
        callbacks = [self.goodbye(), self.client.close()]
        if isinstance(self._tg_app, BaseProxy):
            callbacks.append(self._shutdown_tg_app())
        self.loop.run_until_complete(asyncio.gather(*callbacks))

    async def _shutdown_tg_app(self) -> None:
        self.telegram_proxy_application.dispatcher.stop_polling()  # type: ignore
        await self.telegram_proxy_application.dispatcher.storage.close()  # type: ignore
        await self.telegram_proxy_application.dispatcher.storage.wait_closed()  # type: ignore
        await self.telegram_proxy_application.dispatcher.bot.session.close()  # type: ignore

    async def process_events(self, history: List[Transaction]) -> None:
        """Processing events and send callbacks to handlers"""
        for event in history:
            if cast(int, self.offset) < event.id:
                await self.dispatcher.feed_event(event)
                self.offset = event.id
                self.get_updates_until = self.get_updates_from

    def start_polling(
            self,
            *,
            get_updates_from: Optional[datetime] = None,
            timeout: Union[float, int, ClientTimeout] = DEFAULT_TIMEOUT,
    ) -> None:
        loop: asyncio.AbstractEventLoop = self.loop
        try:
            loop.run_until_complete(self.welcome())
            loop.create_task(self._start_polling(get_updates_from=get_updates_from, timeout=timeout))
            if isinstance(self.telegram_proxy_application, BaseProxy):
                self.telegram_proxy_application.setup(loop=loop)
            run_forever_safe(loop=loop)
        except (SystemExit, KeyboardInterrupt):  # pragma: no cover
            # Allow to graceful shutdown
            pass  # pragma: no cover
        finally:
            self._on_shutdown()

    def start_webhook(
            self,
            *,
            host: str = "localhost",
            port: int = 8080,
            path: Optional[Path] = None,
            app: Optional[web.Application] = None,
            ssl_context: Optional[SSLContext] = None,
    ) -> None:
        loop: asyncio.AbstractEventLoop = self.loop
        application = app or web.Application()
        hook_config, key = loop.run_until_complete(self.client.bind_webhook())
        application = server.setup(
            dispatcher=self.dispatcher,
            app=application,
            path=path,
            secret_key=self.client.secret_p2p,
            base64_key=key,
            tg_app=self.telegram_proxy_application,
        )
        try:
            loop.run_until_complete(self.welcome())
            web.run_app(application, host=host, port=port, ssl_context=ssl_context)
        except (KeyboardInterrupt, SystemExit):
            # Allow to graceful shutdown
            pass
        finally:
            self._on_shutdown()

    async def welcome(self) -> None:
        self.dispatcher.logger.debug("Executor has started work!")
        for callback in self._on_startup_calls:
            await _inspect_and_execute_callback(
                callback=callback, client=self.client
            )  # pragma: no cover

    async def goodbye(self) -> None:
        self.dispatcher.logger.debug("Goodbye!")
        for callback in self._on_shutdown_calls:
            await _inspect_and_execute_callback(
                callback=callback, client=self.client
            )  # pragma: no cover
