"""
Managing polling and webhooks
"""
from __future__ import annotations

import abc
import asyncio
import inspect
import logging
import types
from datetime import datetime, timedelta
from functools import wraps
from ssl import SSLContext
from typing import (
    Union,
    Optional,
    List,
    Callable,
    TypeVar,
    TYPE_CHECKING,
    Any,
    cast,
)

from aiohttp import web
from mypy_extensions import KwArg, VarArg

from glQiwiApi.builtin import BaseProxy
from glQiwiApi.builtin import logger
from glQiwiApi.core.constants import (
    DEFAULT_TIMEOUT,
    TIMEOUT_IF_EXCEPTION,
    DEFAULT_APPLICATION_KEY,
)
from glQiwiApi.core.dispatcher.webhooks import server
from glQiwiApi.core.dispatcher.webhooks.config import Path
from glQiwiApi.core.synchronous import adapter
from glQiwiApi.types import Transaction
from glQiwiApi.utils.exceptions import NoUpdatesToExecute, BadCallback

__all__ = ["start_webhook", "start_polling"]

if TYPE_CHECKING:
    from glQiwiApi.qiwi.client import QiwiWrapper  # pragma: no cover

T = TypeVar("T")

_CallbackType = Callable[["QiwiWrapper", VarArg(), KwArg()], T]


def _parse_timeout(timeout: Union[float, int]) -> float:
    if isinstance(timeout, float):
        return timeout
    elif isinstance(timeout, int):
        return float(timeout)
    else:
        raise TypeError(f"Timeout must be float or int. You have passed on {type(timeout)}")


async def _inspect_and_execute_callback(
        client: "QiwiWrapper", callback: Callable[[QiwiWrapper], Any]
) -> None:
    if inspect.iscoroutinefunction(callback):
        await callback(client)
    else:
        callback(client)  # pragma: no cover


def _warn_on_long_close(log: logging.Logger) -> None:
    log.warning('Callback is taking over 60 seconds to complete. '
                'Check if you have any unreleased connections left. '
                'Use asyncio.wait_for() to set a timeout for callback')


def _patch_callback(callback: _CallbackType[T], loop: asyncio.AbstractEventLoop) -> _CallbackType[T]:
    if not isinstance(callback, types.FunctionType):
        raise BadCallback("Callback passed to on_startup / on_shutdown is not a function")

    @wraps(callback)
    async def patched_callback(c: QiwiWrapper, *args, **kwargs) -> Any:
        loop.call_later(60, _warn_on_long_close, c.dispatcher.logger)
        return await callback(c, *args, **kwargs)

    return patched_callback


def _setup_callbacks(
        executor: BaseExecutor,
        on_startup: Optional[_CallbackType[Any]] = None,
        on_shutdown: Optional[_CallbackType[Any]] = None,
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


def start_webhook(
        client: QiwiWrapper,
        *,
        host: str = "localhost",
        port: int = 8080,
        path: Optional[Path] = None,
        on_startup: Optional[_CallbackType[Any]] = None,
        on_shutdown: Optional[_CallbackType[Any]] = None,
        tg_app: Optional[BaseProxy] = None,
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
          or class, that inherits from BaseProxy
          and deal with foreign framework/application in the background
    :param ssl_context:
    :param loop:
    """
    executor = WebhookExecutor(client, tg_app=tg_app, loop=loop)
    _setup_callbacks(executor, on_startup, on_shutdown)
    executor.start_webhook(
        host=host, port=port, path=path, app=app, ssl_context=ssl_context
    )


def start_polling(
        client: QiwiWrapper,
        *,
        skip_updates: bool = False,
        timeout: Union[float, int] = 5,
        on_startup: Optional[_CallbackType[Any]] = None,
        on_shutdown: Optional[_CallbackType[Any]] = None,
        tg_app: Optional[BaseProxy] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
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
    :param tg_app: builtin TelegramPollingProxy or other
         class, that inherits from BaseProxy, deal with foreign framework/application
         in the background
    :param loop:
    """
    executor = PollingExecutor(
        client, tg_app=tg_app, timeout=timeout, loop=loop, skip_updates=skip_updates
    )
    _setup_callbacks(executor, on_startup, on_shutdown)
    executor.start_polling()


class BaseExecutor(abc.ABC):
    def __init__(
            self,
            client: QiwiWrapper,
            tg_app: Optional[BaseProxy],
            loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        if loop is not None:
            self._loop = loop  # pragma: no cover

        self._logger_config = {
            "handlers": [logger.InterceptHandler()],
            "level": logging.DEBUG,
        }
        self._tg_app = tg_app
        self.client = client
        self._on_startup_calls: List[_CallbackType[Any]] = []
        self._on_shutdown_calls: List[_CallbackType[Any]] = []

        self._dispatcher = client.dispatcher

    async def welcome(self) -> None:
        self._dispatcher.logger.debug("Executor has started work!")
        for callback in self._on_startup_calls:
            await _inspect_and_execute_callback(
                callback=callback, client=self.client
            )  # pragma: no cover

    async def goodbye(self) -> None:
        self._dispatcher.logger.debug("Goodbye!")
        for callback in self._on_shutdown_calls:
            await _inspect_and_execute_callback(
                callback=callback, client=self.client
            )  # pragma: no cover

    def _create_new_loop_if_closed(self) -> None:
        if self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

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

    def add_shutdown_callback(self, callback: _CallbackType[Any]) -> None:
        self._on_shutdown_calls.append(_patch_callback(callback, self.loop))

    def add_startup_callback(self, callback: _CallbackType[Any]) -> None:
        self._on_startup_calls.append(_patch_callback(callback, self.loop))

    def _on_shutdown(self) -> None:
        """
        On shutdown, executor gracefully cancel all tasks, close event loop
        and call `close` method to clear resources
        """
        callbacks = [self.goodbye(), self.client.close(), self._shutdown_tg_app()]
        self.loop.run_until_complete(asyncio.gather(*callbacks))

    async def _shutdown_tg_app(self) -> None:
        if self._tg_app is None:
            return

        self._tg_app.dispatcher.stop_polling()
        await self._tg_app.dispatcher.storage.close()
        await self._tg_app.dispatcher.storage.wait_closed()
        await self._tg_app.dispatcher.bot.session.close()


class PollingExecutor(BaseExecutor):
    def __init__(
            self,
            client: QiwiWrapper,
            tg_app: Optional[BaseProxy],
            loop: Optional[asyncio.AbstractEventLoop] = None,
            timeout: Union[float, int] = DEFAULT_TIMEOUT,
            skip_updates: bool = False,
    ) -> None:
        """

        :param client: instance of BaseWrapper
        :param tg_app: optional proxy to connect aiogram polling/webhook mode
        """
        super(PollingExecutor, self).__init__(client, tg_app, loop)
        self.offset: Optional[int] = None
        self.get_updates_until: Optional[datetime] = None
        self.get_updates_from: Optional[datetime] = None
        self._timeout: Union[int, float] = _parse_timeout(timeout)
        self.skip_updates = skip_updates

    def start_polling(self) -> None:
        loop: asyncio.AbstractEventLoop = self.loop
        try:
            loop.run_until_complete(self.welcome())
            loop.create_task(self._start_polling())
            if isinstance(self._tg_app, BaseProxy):
                self._tg_app.setup(loop=loop)
            adapter.run_forever_safe(loop=loop)
        except (SystemExit, KeyboardInterrupt):  # pragma: no cover
            # Allow to graceful shutdown
            pass  # pragma: no cover
        finally:
            self._on_shutdown()

    async def _start_polling(self) -> None:
        while True:
            try:
                await self._pool_process()
                self._set_timeout(DEFAULT_TIMEOUT)
            except Exception as ex:
                self._set_timeout(TIMEOUT_IF_EXCEPTION)
                self._dispatcher.logger.error(
                    "Handle `%s`. Sleeping %s seconds", repr(ex), self._timeout
                )
            await asyncio.sleep(self._timeout)

    async def _pool_process(self) -> None:
        await self._prepare_date_boundaries()
        try:
            history_from_last_to_first: List[Transaction] = await self._fetch_updates()
        except NoUpdatesToExecute:
            return
        history_from_first_to_last: List[Transaction] = history_from_last_to_first[::-1]
        if self.offset is None:
            first_payment: Transaction = history_from_first_to_last[0]
            self.offset = first_payment.id - 1
        await self.process_events(history_from_first_to_last)

    async def _prepare_date_boundaries(self) -> None:
        current_time = datetime.now()
        self.get_updates_from = current_time - timedelta(seconds=self._timeout)
        self.get_updates_until = current_time

    async def _fetch_updates(self) -> List[Transaction]:
        history = await self.client.transactions(
            end_date=self.get_updates_until, start_date=self.get_updates_from
        )
        if self.skip_updates:
            self.skip_updates = False
            raise NoUpdatesToExecute()
        elif not history:
            raise NoUpdatesToExecute()
        return history

    async def process_events(self, history: List[Transaction]) -> None:
        tasks: List[asyncio.Task[None]] = [
            asyncio.create_task(self._dispatcher.process_event(event))
            for event in history
            if cast(int, self.offset) < event.id
        ]
        if history:
            self.offset = history[-1].id
        await asyncio.gather(*tasks)

    def _set_timeout(self, exception_timeout: Union[int, float]) -> None:
        self._timeout = exception_timeout


class WebhookExecutor(BaseExecutor):

    def __init__(self,
                 client: QiwiWrapper,
                 tg_app: Optional[BaseProxy],
                 loop: Optional[asyncio.AbstractEventLoop] = None):
        super().__init__(client, tg_app, loop)
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
            secret_key=self.client.secret_p2p,
            tg_app=self._tg_app,
        )
        self._add_application_into_client_data()
        try:
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
