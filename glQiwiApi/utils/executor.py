"""
Managing polling and webhooks
"""
from __future__ import annotations

import abc
import asyncio
import inspect
import logging
import ssl
from datetime import datetime
from typing import (
    Union,
    Optional,
    List,
    Callable,
    TypeVar,
    Any,
    cast,
    Dict, Iterable, Tuple,
)

from aiohttp import web
from aiohttp.web import _run_app

from glQiwiApi.core.dispatcher.webhooks.app import configure_app
from glQiwiApi.core.dispatcher.webhooks.config import WebhookConfig
from glQiwiApi.core.synchronous import adapter
from glQiwiApi.plugins.abc import Pluggable
from glQiwiApi.qiwi.client import QiwiWrapper, MAX_HISTORY_TRANSACTION_LIMIT
from glQiwiApi.types import Transaction
from glQiwiApi.utils.exceptions import SecretP2PTokenIsEmpty

__all__ = ["start_webhook", "start_polling"]

T = TypeVar("T")

logger = logging.getLogger("glQiwiApi.executor")

TIMEOUT_IF_EXCEPTION = 40
DEFAULT_TIMEOUT = 5

DEFAULT_APPLICATION_KEY = "__aiohttp_web_application__"


class NoUpdatesToExecute(Exception):
    """Internal exception to determine that history is empty"""


class ExecutorEvent:
    def __init__(self, context: Any, init_handlers: Iterable[Optional[Callable[..., Any]]] = ()) -> None:
        self._handlers: List[Tuple[Callable[..., Any], bool]] = []
        for handler in init_handlers:
            if handler is None:
                continue
            is_awaitable = inspect.isawaitable(handler) or inspect.iscoroutinefunction(handler)
            self._handlers.append((handler, is_awaitable))
        self.context = context

    def __iadd__(self, handler: Callable[..., Any]) -> "ExecutorEvent":
        self._handlers.append((handler, inspect.isawaitable(handler) or inspect.iscoroutinefunction(handler)))
        return self

    def __isub__(self, handler: Callable[..., Any]) -> "ExecutorEvent":
        self._handlers.remove((handler, inspect.isawaitable(handler) or inspect.iscoroutinefunction(handler)))
        return self

    def __len__(self) -> int:
        return len(self._handlers)

    def __call__(self, *args: Any) -> Any:
        if args:
            self.__iadd__(args[0])
            return args[0]

        def decorator(fn):
            self.__iadd__(fn)
            return fn

        return decorator

    async def fire(self, *args: Any, **kwargs: Any) -> None:
        for handler, awaitable in self._handlers:
            if awaitable:
                await handler(self.context, *args, **kwargs)
            else:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, handler)


def start_webhook(
        client: QiwiWrapper,
        *plugins: Pluggable,
        webhook_config: WebhookConfig = WebhookConfig(),
        on_startup: Optional[Callable[..., Any]] = None,
        on_shutdown: Optional[Callable[..., Any]] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None
) -> None:
    """
    Blocking function that listens for webhooks

    :param client: instance of QiwiWrapper
    :param on_startup: coroutine,which will be executed on startup
    :param on_shutdown: coroutine, which will be executed on shutdown
    :param webhook_config:
    :param plugins: List of plugins, that will be executed together with polling.
         For example  builtin TelegramWebhookPlugin or other
         class, that inherits from BaseProxy, deal with foreign framework/application
         in the background
    :param loop:
    """
    executor = WebhookExecutor(client, *plugins, on_shutdown=on_shutdown, on_startup=on_startup,
                               loop=loop)
    executor.start_webhook(config=webhook_config)


def start_polling(
        client: QiwiWrapper,
        *plugins: Pluggable,
        skip_updates: bool = False,
        timeout: float = DEFAULT_TIMEOUT,
        on_startup: Optional[Callable[..., Any]] = None,
        on_shutdown: Optional[Callable[..., Any]] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None
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
         For example  builtin TelegramPollingPlugin or other
         class, that inherits from BaseProxy, deal with foreign framework/application
         in the background
    :param loop:
    """
    executor = PollingExecutor(
        client, *plugins, timeout=timeout, skip_updates=skip_updates,
        on_startup=on_startup, on_shutdown=on_shutdown, loop=loop
    )
    executor.start_polling()


class BaseExecutor(abc.ABC):
    def __init__(self, client: QiwiWrapper, *plugins: Pluggable,
                 loop: Optional[asyncio.AbstractEventLoop] = None,
                 on_startup: Optional[Callable[..., Any]] = None,
                 on_shutdown: Optional[Callable[..., Any]] = None) -> None:
        if loop is not None:
            self._loop = loop  # pragma: no cover
        self._client = client
        self._on_startup = ExecutorEvent(client, init_handlers=[on_startup])
        self._on_shutdown = ExecutorEvent(client, init_handlers=[on_shutdown])
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
        logger.info("Executor has started work!")
        await self._on_startup.fire()

    async def goodbye(self) -> None:
        logger.info("Goodbye!")
        await self._on_shutdown.fire()

    async def _install_plugins(self, ctx: Optional[Dict[Any, Any]] = None) -> None:
        if ctx is None:
            ctx = {}
        incline_tasks = [plugin.install(ctx) for plugin in self._plugins]
        await asyncio.shield(asyncio.gather(*incline_tasks))

    async def _shutdown(self) -> None:
        """
        On shutdown, executor gracefully cancel all tasks, close event loop
        and call `close` method to clear resources
        """
        callbacks = [self.goodbye(), self._client.close(), self._shutdown_plugins()]
        await asyncio.gather(*callbacks)

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
            on_startup: Optional[Callable[..., Any]] = None,
            on_shutdown: Optional[Callable[..., Any]] = None
    ) -> None:
        """

        :param client: instance of BaseWrapper
        :param tg_app: optional proxy to connect aiogram polling/webhook mode
        """
        super(PollingExecutor, self).__init__(client, *plugins, loop=loop, on_startup=on_startup,
                                              on_shutdown=on_shutdown)
        self.offset: Optional[int] = None
        self.get_updates_from = datetime.now()
        self._timeout: Union[int, float] = _parse_timeout(timeout)
        self.skip_updates = skip_updates

    def start_polling(self) -> None:
        try:
            self.loop.run_until_complete(self.welcome())
            self.loop.create_task(self._install_plugins())
            self.loop.create_task(self._run_infinite_polling())
            adapter.run_forever_safe(self.loop)
        except (SystemExit, KeyboardInterrupt):  # pragma: no cover
            # allow graceful shutdown
            pass
        finally:
            self.loop.run_until_complete(self.goodbye())

    async def _run_infinite_polling(self) -> None:
        default_timeout = self._timeout
        while True:
            try:
                await self._try_fetch_new_updates()
                self._set_timeout(default_timeout)
            except Exception as ex:
                self._set_timeout(TIMEOUT_IF_EXCEPTION)
                logger.error("Handle !r. Sleeping %s seconds", ex, self._timeout)
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
            raise NoUpdatesToExecute()

        return history

    async def _get_consistent_history(self) -> List[Transaction]:
        """
        QIWI API returns history sorted by dates descending, but for "consistency" we have to reverse it,
        which is what this method does.
        """
        history_from_last_to_first = await self._client.transactions(
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

    def __init__(self, client: QiwiWrapper, *plugins: Pluggable,
                 on_startup: Optional[Callable[..., Any]] = None,
                 on_shutdown: Optional[Callable[..., Any]] = None,
                 loop: Optional[asyncio.AbstractEventLoop] = None):
        super().__init__(client, *plugins, on_startup=on_startup, on_shutdown=on_shutdown, loop=loop)
        self._application = web.Application(loop=self.loop)

    def start_webhook(self, config: WebhookConfig) -> None:
        if config.app.base_app is not None:
            self._application = config.app.base_app

        if self._client._secret_p2p is None:
            if config.encryption.secret_p2p_key is None:
                raise SecretP2PTokenIsEmpty(
                    "Secret p2p token is empty, cannot setup webhook without it. "
                    "Please, provide token to work with webhooks."
                )
            config.encryption.secret_p2p_key = self._client._secret_p2p

        if config.encryption.base64_encryption_key is None:
            config.encryption.base64_encryption_key = self.loop.run_until_complete(
                self._get_webhook_encryption_key()
            )

        self._application = configure_app(
            dispatcher=self._dispatcher,
            app=self._application,
            webhook_config=config
        )

        cert = config.app.ssl_certificate
        ssl_context: Optional[ssl.SSLContext] = None
        if cert is not None:
            ssl_context = cert.as_ssl_context()

        self._add_application_into_client_data()

        self.loop.create_task(self._install_plugins())
        try:
            self.loop.run_until_complete(self.welcome())
            self.loop.create_task(
                _run_app(
                    app=self._application,
                    host=config.app.host,
                    port=config.app.port,
                    ssl_context=ssl_context,
                    **config.app.kwargs
                )
            )
            adapter.run_forever_safe(self.loop)
        finally:
            self.loop.run_until_complete(self.goodbye())

    async def _get_webhook_encryption_key(self) -> str:
        current_webhook = await self._client.get_current_webhook()
        return await self._client.get_webhook_secret_key(current_webhook.id)

    def _add_application_into_client_data(self) -> None:
        self._client[DEFAULT_APPLICATION_KEY] = self._application


def _parse_timeout(timeout: Union[float, int]) -> float:
    if isinstance(timeout, float):
        return timeout
    elif isinstance(timeout, int):
        return float(timeout)
    else:
        raise TypeError(f"Timeout must be float or int. You have passed on {type(timeout)}")
