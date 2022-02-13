from __future__ import annotations

import abc
import asyncio
import inspect
import logging
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Union, cast, Awaitable

from aiohttp import web
from aiohttp.web import _run_app  # noqa

from glQiwiApi import QiwiWrapper
from glQiwiApi.core.event_fetching.dispatcher import BaseDispatcher
from glQiwiApi.core.event_fetching.webhooks.app import configure_app
from glQiwiApi.core.event_fetching.webhooks.config import WebhookConfig
from glQiwiApi.utils.synchronous import adapter
from glQiwiApi.ext.webhook_url import WebhookURL
from glQiwiApi.plugins.abc import Pluggable
from glQiwiApi.qiwi.clients.wallet.client import QiwiWallet
from glQiwiApi.qiwi.clients.wallet.methods.history import MAX_HISTORY_LIMIT
from glQiwiApi.qiwi.clients.wallet.types import History

logger = logging.getLogger("glQiwiApi.executor")

TIMEOUT_IF_EXCEPTION = 40
DEFAULT_TIMEOUT = 5
WALLET_CTX_KEY = "wallet"


class _NoUpdatesToExecute(Exception):
    """Internal exception to determine that history is empty"""


_EventHandlerType = Callable[["Context"], Union[None, Awaitable[None]]]


@dataclass
class _HandlerSpec:
    handler_fn: Callable[..., Any]

    @property
    def is_awaitable(self) -> bool:
        return inspect.isawaitable(self.handler_fn) or inspect.iscoroutinefunction(self.handler_fn)


class ExecutorEvent:
    def __init__(
        self,
        context: Context,
        init_handlers: Iterable[Optional[_EventHandlerType]] = (),
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        self._handlers: List[_HandlerSpec] = []
        for handler in init_handlers:
            if handler is None:
                continue
            self._handlers.append(_HandlerSpec(handler))
        self.context = context
        self._loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()

    def __iadd__(self, handler: Callable[..., Any]) -> "ExecutorEvent":
        self._handlers.append(_HandlerSpec(handler))
        return self

    def __isub__(self, handler: Callable[..., Any]) -> "ExecutorEvent":
        self._handlers.remove(_HandlerSpec(handler))
        return self

    def __len__(self) -> int:
        return len(self._handlers)

    async def fire(self) -> None:
        for handler_spec in self._handlers:
            if handler_spec.is_awaitable:
                return await handler_spec.handler_fn(self.context)  # type: ignore
            await self._loop.run_in_executor(None, handler_spec.handler_fn, self.context)


def start_webhook(
    wallet: Union[QiwiWallet, QiwiWrapper],
    dispatcher: BaseDispatcher,
    *plugins: Pluggable,
    webhook_config: WebhookConfig,
    on_startup: Optional[_EventHandlerType] = None,
    on_shutdown: Optional[_EventHandlerType] = None,
    loop: Optional[asyncio.AbstractEventLoop] = None,
    context: Union[Dict[str, Any], Context, None] = None,
) -> None:
    """
    Blocking function that listens for webhooks.
    Supports only `glQiwiApi.types.BillWebhook` and `glQiwiApi.types.TransactionWebhook`

    :param wallet: instance of QiwiWrapper
    :param dispatcher:
    :param on_startup: coroutine,which will be executed on startup
    :param on_shutdown: coroutine, which will be executed on shutdown
    :param webhook_config:
    :param plugins: List of plugins, that will be executed together with polling.
         For example  builtin TelegramWebhookPlugin or other
         class, that implement Pluggable abc interface, deal with foreign framework/application
         in the background
    :param loop:
    :param context: context, that could be transmitted to handlers
    """
    if context is None:
        context = {}
    executor = WebhookExecutor(
        wallet,
        dispatcher,
        *plugins,
        on_shutdown=on_shutdown,
        on_startup=on_startup,
        loop=loop,
        context=Context(context),
    )
    executor.start_webhook(config=webhook_config)


def start_polling(
    wallet: Union[QiwiWallet, QiwiWrapper],
    dispatcher: BaseDispatcher,
    *plugins: Pluggable,
    skip_updates: bool = False,
    timeout_in_seconds: float = DEFAULT_TIMEOUT,
    on_startup: Optional[_EventHandlerType] = None,
    on_shutdown: Optional[_EventHandlerType] = None,
    loop: Optional[asyncio.AbstractEventLoop] = None,
    context: Union[Dict[str, Any], Context, None] = None,
) -> None:
    """
    Setup for long-polling mode. Support only `glQiwiApi.types.Transaction` as event.

    :param wallet: instance of QiwiWrapper
    :param dispatcher:
    :param skip_updates:
    :param timeout_in_seconds: timeout of polling in seconds, if the timeout is too small,
         the API can throw an exception
    :param on_startup: function or coroutine,
         which will be executed on startup
    :param on_shutdown: function or coroutine,
         which will be executed on shutdown
    :param plugins: List of plugins, that will be executed together with polling.
         For example  builtin TelegramPollingPlugin or other
         class, that implement Pluggable abc interface, deal with foreign framework/application
         in the background
    :param loop:
    :param context: context, that could be transmitted to handlers
    """
    if context is None:
        context = {}
    executor = PollingExecutor(
        wallet,
        dispatcher,
        *plugins,
        timeout=timeout_in_seconds,
        skip_updates=skip_updates,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        loop=loop,
        context=Context(context),
    )
    executor.start_polling()


async def start_non_blocking_qiwi_api_polling(
    wallet: Union[QiwiWallet, QiwiWrapper],
    dispatcher: BaseDispatcher,
    skip_updates: bool = False,
    timeout_in_seconds: float = DEFAULT_TIMEOUT,
    on_startup: Optional[_EventHandlerType] = None,
    on_shutdown: Optional[_EventHandlerType] = None,
    loop: Optional[asyncio.AbstractEventLoop] = None,
    context: Union[Dict[str, Any], Context, None] = None,
) -> None:
    if context is None:
        context = {}
    executor = PollingExecutor(
        wallet,
        dispatcher,
        timeout=timeout_in_seconds,
        skip_updates=skip_updates,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        loop=loop,
        context=Context(context),
    )
    await executor.start_non_blocking_polling()


def configure_app_for_qiwi_webhooks(
    wallet: Union[QiwiWallet, QiwiWrapper],
    dispatcher: BaseDispatcher,
    app: web.Application,
    cfg: WebhookConfig,
) -> web.Application:
    executor = WebhookExecutor(wallet, dispatcher, context=Context({}))
    return executor.add_routes_for_webhook(app, cfg)


class Context(Dict[str, Any]):
    def __getattr__(self, item: str) -> Any:
        return self[item]

    @property
    def wallet(self) -> Union[QiwiWallet, QiwiWrapper]:
        return cast(Union[QiwiWallet, QiwiWrapper], self[WALLET_CTX_KEY])


class BaseExecutor(abc.ABC):
    def __init__(
        self,
        dispatcher: BaseDispatcher,
        *plugins: Pluggable,
        context: Context,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        on_startup: Optional[Callable[..., Any]] = None,
        on_shutdown: Optional[Callable[..., Any]] = None,
    ) -> None:
        if loop is not None:
            self._loop = loop  # pragma: no cover
        self._on_startup = ExecutorEvent(context, init_handlers=[on_startup], loop=self.loop)
        self._on_shutdown = ExecutorEvent(context, init_handlers=[on_shutdown], loop=self.loop)
        self._dispatcher = dispatcher
        self._plugins = plugins
        self._context = context

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
        await asyncio.gather(*incline_tasks)

    async def _shutdown(self) -> None:
        """
        On shutdown, executor gracefully cancel all tasks, close event loop
        and call `close` method to clear resources
        """
        callbacks = [self.goodbye(), self._shutdown_plugins()]
        await asyncio.shield(asyncio.gather(*callbacks))

    async def _shutdown_plugins(self) -> None:
        logger.debug("Shutting down plugins")
        shutdown_tasks = [asyncio.create_task(plugin.shutdown()) for plugin in self._plugins]
        await asyncio.gather(*shutdown_tasks)


class PollingExecutor(BaseExecutor):
    def __init__(
        self,
        wallet: Union[QiwiWallet, QiwiWrapper],
        dispatcher: BaseDispatcher,
        *plugins: Pluggable,
        context: Context,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        timeout: Union[float, int] = DEFAULT_TIMEOUT,
        skip_updates: bool = False,
        on_startup: Optional[_EventHandlerType] = None,
        on_shutdown: Optional[_EventHandlerType] = None,
    ) -> None:
        super(PollingExecutor, self).__init__(
            dispatcher,
            *plugins,
            loop=loop,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            context=context,
        )
        self.offset: Optional[int] = None
        self.get_updates_from = datetime.now()
        self._timeout = _parse_timeout(timeout)
        self.skip_updates = skip_updates
        self._wallet = wallet

        self._context[WALLET_CTX_KEY] = self._wallet

    def start_polling(self) -> None:
        try:
            asyncio.ensure_future(
                asyncio.gather(self._install_plugins(), self._run_infinite_polling())
            )
            adapter.run_forever_safe(self.loop)
        except (SystemExit, KeyboardInterrupt):  # pragma: no cover
            # allow graceful shutdown
            pass

    async def start_non_blocking_polling(self) -> None:
        asyncio.create_task(self._run_infinite_polling())

    async def _run_infinite_polling(self) -> None:
        default_timeout = self._timeout

        try:
            await self.welcome()
            while True:
                try:
                    await self._try_fetch_new_updates()
                    self._set_timeout(default_timeout)
                except Exception as ex:
                    self._set_timeout(TIMEOUT_IF_EXCEPTION)
                    logger.error("Handle !r. Sleeping %s seconds", ex, self._timeout)
                await asyncio.sleep(self._timeout)
        finally:
            await asyncio.shield(asyncio.gather(self.goodbye(), self._wallet.close()))

    async def _try_fetch_new_updates(self) -> None:
        try:
            history = await self._fetch_history()
        except _NoUpdatesToExecute:
            return None
        if self.offset is None:
            first_update = history[0]
            self.offset = first_update.id - 1
        logger.debug("Current transaction offset is %d", self.offset)
        await self.process_updates(history)

    async def _fetch_history(self) -> History:
        if isinstance(self._wallet, QiwiWallet):
            history = (
                await self._wallet.history(
                    start_date=self.get_updates_from, end_date=datetime.now()
                )
            ).sorted_by_date()
        else:
            history = (
                await self._wallet.transactions(
                    start_date=self.get_updates_from, end_date=datetime.now()
                )
            ).sorted_by_date()

        if len(history) == MAX_HISTORY_LIMIT:
            logger.debug("History is out of max history transaction limit")
            first_txn_by_date = history[-1]
            self.get_updates_from = first_txn_by_date.date

        if self.skip_updates:
            self.skip_updates = False
            raise _NoUpdatesToExecute()
        elif not history:
            raise _NoUpdatesToExecute()

        return history

    async def process_updates(self, history: History) -> None:
        tasks: List[asyncio.Task[None]] = [
            asyncio.create_task(self._dispatcher.process_event(event, self._context))
            for event in history
            if cast(int, self.offset) < event.id
        ]
        if history:
            self.offset = history.sorted_by_id().last().id
        await asyncio.gather(*tasks)

    def _set_timeout(self, exception_timeout: Union[int, float]) -> None:
        self._timeout = exception_timeout

    async def _shutdown(self) -> None:
        await asyncio.gather(super()._shutdown(), self._wallet.close())


class WebhookExecutor(BaseExecutor):
    def __init__(
        self,
        wallet: Union[QiwiWallet, QiwiWrapper],
        dispatcher: BaseDispatcher,
        *plugins: Pluggable,
        context: Context,
        on_startup: Optional[_EventHandlerType] = None,
        on_shutdown: Optional[_EventHandlerType] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        super().__init__(
            dispatcher,
            *plugins,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            loop=loop,
            context=context,
        )
        self._application = web.Application(loop=self.loop)
        self._wallet = wallet

        self._context[WALLET_CTX_KEY] = self._wallet

    def add_routes_for_webhook(
        self, app: web.Application, config: WebhookConfig
    ) -> web.Application:
        supplemented_configuration = self.loop.run_until_complete(
            self._supplement_configuration(config)
        )
        try:
            return configure_app(
                dispatcher=self._dispatcher,
                app=app,
                webhook_config=supplemented_configuration,
            )
        finally:
            self.loop.run_until_complete(self._wallet.close())

    def start_webhook(self, config: WebhookConfig) -> None:
        supplemented_configuration = self.loop.run_until_complete(
            self._supplement_configuration(config)
        )

        self._application = configure_app(
            dispatcher=self._dispatcher,
            app=self._application,
            webhook_config=supplemented_configuration,
        )

        self.loop.create_task(self._install_plugins())
        try:
            self.loop.run_until_complete(self.welcome())
            self.loop.create_task(
                _run_app(
                    app=self._application,
                    host=supplemented_configuration.app.host,
                    port=supplemented_configuration.app.port,
                    ssl_context=supplemented_configuration.app.ssl_context,
                    **supplemented_configuration.app.kwargs,
                )
            )
            adapter.run_forever_safe(self.loop)
        finally:
            self.loop.run_until_complete(self.goodbye())

    async def _supplement_configuration(self, config: WebhookConfig) -> WebhookConfig:
        config = deepcopy(config)
        if config.app.base_app is not None:
            self._application = config.app.base_app

        if config.encryption.secret_p2p_key is None:
            raise RuntimeError(
                "Secret p2p token is empty, cannot setup webhook without it. "
                "Please, provide token to work with webhooks."
            )

        await self._set_base64_encryption_key_for_config(config)
        return config

    async def _set_base64_encryption_key_for_config(self, config: WebhookConfig) -> None:
        if config.encryption.base64_encryption_key is None:
            if config.hook_registration.host_or_ip_address is None:
                raise RuntimeError(
                    "You didn't transmit neither base64 "
                    "encryption key to WebhookConfig nor host or ip address to bind new webhook."
                    "To fix it, pass on WebhookConfig.hook_registration.host_or_ip_address or "
                    "WebhookConfig.encryption.base64_encryption_key to executor.start_webhook(...)"
                )
            _, base64_encryption_key = await self._wallet.bind_webhook(
                url=WebhookURL.create(
                    host=config.hook_registration.host_or_ip_address,
                    port=config.app.port,
                    webhook_path=config.routes.standard_qiwi_hook_path[1:],
                    https=config.app.ssl_context is not None,
                ),
                delete_old=True,
            )
            config.encryption.base64_encryption_key = base64_encryption_key


def _parse_timeout(timeout: Union[float, int]) -> float:  # pragma: no cover
    if isinstance(timeout, float):
        return timeout
    elif isinstance(timeout, int):
        return float(timeout)
    else:
        raise TypeError(f"Timeout must be float or int. You have passed on {type(timeout)}")
