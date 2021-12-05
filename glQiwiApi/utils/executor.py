"""
Managing polling and webhooks
"""
from __future__ import annotations

import abc
import asyncio
import inspect
import logging
from datetime import datetime
from ssl import SSLContext
from typing import (
    Union,
    Optional,
    List,
    Callable,
    TypeVar,
    Any,
    cast,
    Dict,
)

from aiohttp import web

from glQiwiApi.core.constants import (
    DEFAULT_TIMEOUT,
    TIMEOUT_IF_EXCEPTION,
    DEFAULT_APPLICATION_KEY,
)
from glQiwiApi.core.dispatcher.webhooks import server
from glQiwiApi.core.dispatcher.webhooks.config import Path
from glQiwiApi.core.synchronous import adapter
from glQiwiApi.plugins.abc import Pluggable
from glQiwiApi.qiwi.client import QiwiWrapper, MAX_HISTORY_TRANSACTION_LIMIT  # pragma: no cover
from glQiwiApi.types import Transaction
from glQiwiApi.utils.exceptions import NoUpdatesToExecute

__all__ = ["start_webhook", "start_polling"]

T = TypeVar("T")

_CallbackType = Callable[..., Any]

logger = logging.getLogger("glQiwiApi.executor")


def start_webhook(
        client: QiwiWrapper,
        *plugins: Pluggable,
        host: str = "localhost",
        port: int = 8080,
        path: Optional[Path] = None,
        on_startup: Optional[_CallbackType] = None,
        on_shutdown: Optional[_CallbackType] = None,
        app: Optional["web.Application"] = None,
        ssl_context: Optional[SSLContext] = None
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
    :param plugins: List of plugins, that will be executed together with polling.
         For example  builtin TelegramPollingProxy or other
         class, that inherits from BaseProxy, deal with foreign framework/application
         in the background
    :param ssl_context:
    """
    executor = WebhookExecutor(client, *plugins)
    _setup_callbacks(executor, on_startup, on_shutdown)
    executor.start_webhook(
        host=host, port=port, path=path, app=app, ssl_context=ssl_context
    )


def start_polling(
        client: QiwiWrapper,
        *plugins: Pluggable,
        skip_updates: bool = False,
        timeout: float = DEFAULT_TIMEOUT,
        on_startup: Optional[_CallbackType] = None,
        on_shutdown: Optional[_CallbackType] = None
) -> None:
    """
    Setup for long-polling mode. Support only `glQiwiApi.types.Transaction` as event.

    :param client: instance of QiwiWrapper
    :param skip_updates:
    :param timeout: timeout of polling in seconds, if the timeout is too small,
         the API can throw an exception
    :param on_startup: function or coroutine,
         which will be executed on startup
    :param on_shutdown: function or coroutine,
         which will be executed on shutdown
    :param plugins: List of plugins, that will be executed together with polling.
         For example  builtin TelegramPollingProxy or other
         class, that inherits from BaseProxy, deal with foreign framework/application
         in the background
    """
    executor = PollingExecutor(
        client, *plugins, timeout=timeout, skip_updates=skip_updates
    )
    _setup_callbacks(executor, on_startup, on_shutdown)
    executor.start_polling()


class BaseExecutor(abc.ABC):
    def __init__(self, client: QiwiWrapper, *plugins: Pluggable,
                 loop: Optional[asyncio.AbstractEventLoop] = None, ) -> None:
        if loop is not None:
            self._loop = loop  # pragma: no cover
        self.client = client
        self._on_startup_calls: List[_CallbackType] = []
        self._on_shutdown_calls: List[_CallbackType] = []
        self._dispatcher = client.dispatcher
        self._plugins = plugins

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        self._loop = cast(
            asyncio.AbstractEventLoop, getattr(self, "_loop", asyncio.get_event_loop())
        )
        # There is a issue, connected with aiohttp.web application, because glQiwiApi wants to have the same interface
        # for polling and webhooks on_startup & on_shutdown callbacks,
        # so we don't use app.on_shutdown.append(...), on the contrary we use self-written
        # system of callbacks, and so aiohttp.web.Application close event loop on shutdown, that's why we need to
        # create new event loop to gracefully execute shutdown callback.
        # It is highly undesirable to delete this line because you will always catch RuntimeWarning and RuntimeError.
        self._create_new_loop_if_closed()
        return self._loop

    def _create_new_loop_if_closed(self) -> None:
        if self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

    async def welcome(self) -> None:
        logger.debug("Executor has started work!")
        for callback in self._on_startup_calls:
            await _inspect_and_execute_callback(callback=callback, client=self.client)  # pragma: no cover

    async def goodbye(self) -> None:
        logger.debug("Goodbye!")
        for callback in self._on_shutdown_calls:
            await _inspect_and_execute_callback(callback=callback, client=self.client)  # pragma: no cover

    def add_shutdown_callback(self, callback: _CallbackType) -> None:
        self._on_shutdown_calls.append(callback)

    def add_startup_callback(self, callback: _CallbackType) -> None:
        self._on_startup_calls.append(callback)

    async def _incline_plugins(self, ctx: Dict[Any, Any]) -> None:
        incline_tasks = [plugin.incline(ctx) for plugin in self._plugins]
        await asyncio.gather(*incline_tasks)

    def _on_shutdown(self) -> None:
        """
        On shutdown, executor gracefully cancel all tasks, close event loop
        and call `close` method to clear resources
        """
        callbacks = [self.goodbye(), self.client.close(), self._shutdown_plugins()]
        self._loop.run_until_complete(asyncio.shield(asyncio.gather(*callbacks)))

    async def _shutdown_plugins(self) -> None:
        logger.debug("Shutting down plugins")
        shutdown_tasks = [asyncio.create_task(plugin.shutdown()) for plugin in self._plugins]
        await asyncio.gather(*shutdown_tasks)


class PollingExecutor(BaseExecutor):
    def __init__(
            self,
            client: QiwiWrapper,
            *plugins: Pluggable,
            loop: Optional[asyncio.AbstractEventLoop] = None,
            timeout: Union[float, int] = DEFAULT_TIMEOUT,
            skip_updates: bool = False,
    ) -> None:
        """

        :param client: instance of BaseWrapper
        :param tg_app: optional proxy to connect aiogram polling/webhook mode
        """
        super(PollingExecutor, self).__init__(client, *plugins, loop=loop)
        self.offset: Optional[int] = None
        self.get_updates_from = datetime.now()
        self._timeout: Union[int, float] = _parse_timeout(timeout)
        self.skip_updates = skip_updates

    def start_polling(self) -> None:
        loop: asyncio.AbstractEventLoop = self.loop
        try:
            loop.run_until_complete(self.welcome())
            loop.create_task(self._start_polling())
            adapter.run_forever_safe(loop=loop)
        except (SystemExit, KeyboardInterrupt):  # pragma: no cover
            # Allow to graceful shutdown
            pass  # pragma: no cover
        finally:
            self._on_shutdown()

    async def _start_polling(self) -> None:
        default_timeout = self._timeout
        while True:
            try:
                await self._try_fetch_new_updates()
                self._set_timeout(default_timeout)
            except Exception as ex:
                self._set_timeout(TIMEOUT_IF_EXCEPTION)
                logger.error("Handle `!r`. Sleeping %s seconds", ex, self._timeout)
            await asyncio.sleep(self._timeout)

    async def _try_fetch_new_updates(self) -> None:
        try:
            updates = await self._fetch_updates()
        except NoUpdatesToExecute:
            return
        if self.offset is None:
            first_update = updates[0]
            self.offset = first_update.id - 1
        logger.debug("Current transaction offset is %d", self.offset)
        await self.process_updates(updates)

    async def _fetch_updates(self) -> List[Transaction]:
        history = await self._get_consistent_history()
        if len(history) == MAX_HISTORY_TRANSACTION_LIMIT:
            logger.debug("History is out of max history transaction limit")
            first_txn_by_date = history[-1]
            self.get_updates_from = first_txn_by_date.date

        if self.skip_updates:
            self.skip_updates = False
            raise NoUpdatesToExecute()
        elif not history:
            logger.debug("History is empty at the time interval %s to %s", self.get_updates_from)
            raise NoUpdatesToExecute()

        return history

    async def _get_consistent_history(self) -> List[Transaction]:
        """
        QIWI API returns history sorted by dates descending, but for "consistency" we have to reverse it,
        which is what this method does.
        """
        history_from_last_to_first = await self.client.transactions(
            start_date=self.get_updates_from,
            end_date=datetime.now()
        )
        history_from_first_to_last = list(reversed(history_from_last_to_first))
        return history_from_first_to_last

    async def process_updates(self, history: List[Transaction]) -> None:
        tasks: List[asyncio.Task[None]] = [
            asyncio.create_task(self._dispatcher.process_event(event))
            for event in history
            if cast(int, self.offset) < event.id
        ]
        if history:
            sorted_history = sorted(history, key=lambda txn: txn.id)
            self.offset = sorted_history[-1].id
        await asyncio.gather(*tasks)

    def _set_timeout(self, exception_timeout: Union[int, float]) -> None:
        self._timeout = exception_timeout


class WebhookExecutor(BaseExecutor):

    def __init__(self, client: QiwiWrapper, *plugins: Pluggable):
        super().__init__(client, *plugins)
        self._application = web.Application()

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
        if app is not None:
            self._application = app
        self._application = server.configure_app(
            dispatcher=self._dispatcher,
            app=self._application,
            path=path,
            secret_key=self.client.secret_p2p
        )
        self._add_application_into_client_data()
        try:
            self._incline_plugins(ctx={"app": self._application})
            loop.run_until_complete(self.welcome())
            web.run_app(self._application, host=host, port=port, ssl_context=ssl_context)
        except (KeyboardInterrupt, SystemExit):
            # Allow to graceful shutdown
            pass
        finally:
            self._on_shutdown()

    def _add_application_into_client_data(self) -> None:
        self.client[DEFAULT_APPLICATION_KEY] = self._application

    async def welcome(self) -> None:
        """
        We have to override `welcome` method to gracefully get webhook base64 encoded key to decode webhook entities.
        It allow you to bind webhook in on_startup callback and don't do it separately
        """
        await super(WebhookExecutor, self).welcome()
        # call to `bind_webhook` without args gives us data about
        # the current webhook config and base64 encoded key to decode webhook entities
        hook_config, base64_key = await self.client.bind_webhook()
        self._application["_base64_key"] = base64_key


def _parse_timeout(timeout: Union[float, int]) -> float:
    if isinstance(timeout, float):
        return timeout
    elif isinstance(timeout, int):
        return float(timeout)
    else:
        raise TypeError(f"Timeout must be float or int. You have passed on {type(timeout)}")


async def _inspect_and_execute_callback(client: "QiwiWrapper", callback: _CallbackType) -> None:
    if inspect.iscoroutinefunction(callback):
        await callback(client)
    else:
        callback(client)  # pragma: no cover


def _setup_callbacks(
        executor: BaseExecutor,
        on_startup: Optional[_CallbackType] = None,
        on_shutdown: Optional[_CallbackType] = None,
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
