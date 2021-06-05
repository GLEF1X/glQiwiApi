"""
Managing polling and webhooks
"""
from __future__ import annotations

import asyncio
import inspect
import logging
import types
from datetime import datetime, timedelta
from typing import Union, Optional, List, \
    Callable, Awaitable, Dict, TypeVar, TYPE_CHECKING, Coroutine, Any

from aiohttp import ClientTimeout, web

from glQiwiApi.core.builtin import BaseProxy, logger
from glQiwiApi.core.constants import DEFAULT_TIMEOUT
from glQiwiApi.core.web_hooks import server
from glQiwiApi.core.web_hooks.config import Path
from glQiwiApi.core.web_hooks.dispatcher import Dispatcher
from glQiwiApi.types import Transaction
from glQiwiApi.utils import basics as api_helper
from glQiwiApi.utils.exceptions import NoUpdatesToExecute

__all__ = ['start_webhook', 'start_polling']

if TYPE_CHECKING:
    from glQiwiApi.qiwi.client import QiwiWrapper

T = TypeVar("T")


def start_webhook(client: QiwiWrapper, *, host: str = "localhost",
                  port: int = 8080,
                  path: Optional[Path] = None,
                  on_startup: Optional[
                      Callable[
                          [QiwiWrapper], Awaitable[None]
                      ]] = None,
                  on_shutdown: Optional[
                      Callable[
                          [QiwiWrapper], Awaitable[None]
                      ]] = None,
                  tg_app: Optional[BaseProxy] = None,
                  app: Optional["web.Application"] = None):
    """
    Blocking function that listens for webhooks

    :param client:
    :param host: server host
    :param port: server port that open for tcp/ip trans.
    :param path: path for qiwi that will send requests
    :param app: pass web.Application
    :param on_startup: coroutine,which will be executed on startup
    :param on_shutdown: coroutine, which will be executed on shutdown
    :param tg_app: builtin TelegramWebhookProxy or other
          or class, that inherits from BaseProxy and deal with aiogram updates
    :param logger_config:
    """
    executor = Executor(client, tg_app=tg_app)
    _setup_callbacks(executor, on_startup, on_shutdown)
    executor.start_webhook(host=host, port=port, path=path, app=app)


def start_polling(client: QiwiWrapper, *, get_updates_from: datetime = datetime.now(),
                  timeout: Union[float, int, ClientTimeout] = 5,
                  on_startup: Optional[
                      Callable[
                          [QiwiWrapper], Any
                      ]] = None,
                  on_shutdown: Optional[
                      Callable[
                          [QiwiWrapper], Any
                      ]] = None,
                  tg_app: Optional[BaseProxy] = None,
                  **kwargs):
    """
    Setup for long-polling mode

    :param client:
    :param get_updates_from: date from which will be polling,
         if it's None, polling will skip all updates
    :param timeout: timeout of polling in seconds, if the timeout is too small,
         the API can throw an exception
    :param kwargs: keyword arguments that you can pass
         into the aiogram `start_polling` method
    :param on_startup: function or coroutine,
         which will be executed on startup
    :param on_shutdown: function or coroutine,
         which will be executed on shutdown
    :param tg_app: builtin TelegramPollingProxy or other
         class, that inherits from BaseProxy, deal with aiogram updates
    """
    executor = Executor(client, tg_app=tg_app)
    _setup_callbacks(executor, on_startup, on_shutdown)
    executor.start_polling(
        get_updates_from=get_updates_from,
        timeout=timeout,
        **kwargs
    )


async def _inspect_and_execute_callback(client, callback: Callable):
    if inspect.iscoroutinefunction(callback):
        await callback(client)
    else:
        callback(client)


def _setup_callbacks(
        executor: Executor,
        on_startup: Optional[Callable] = None,
        on_shutdown: Optional[Callable] = None
):
    """
    Function, which setup callbacks and set it to dispatcher object

    :param executor:
    :param on_startup:
    :param on_shutdown:
    """
    if on_startup is not None:
        executor["on_startup"] = on_startup
    if on_shutdown is not None:
        executor["on_shutdown"] = on_shutdown


def parse_timeout(
        timeout: Union[float, int, ClientTimeout]
) -> float:
    """
    Parse timeout

    :param timeout:
    """
    if isinstance(timeout, float):
        return timeout
    elif isinstance(timeout, int):
        return float(timeout)
    elif isinstance(timeout, ClientTimeout):
        return timeout.total or DEFAULT_TIMEOUT.total
    else:
        raise ValueError("Timeout must be float, int or ClientTimeout. You have "
                         f"passed on {type(timeout)}")


class Executor:
    """
    Provides normal work of webhooks and polling

    """

    def __init__(self, client: QiwiWrapper, tg_app: Optional[BaseProxy]):
        """

        :param client: instance of BaseWrapper
        :param tg_app: optional proxy to connect aiogram polling/webhook mode
        """
        self.dispatcher: Dispatcher = client.dispatcher
        self._loop: asyncio.AbstractEventLoop = client.dispatcher._loop
        self._logger_config: Dict[str, Union[List[logging.Handler], int]] = {
            "handlers": [logger.InterceptHandler()],
            "level": logging.DEBUG
        }
        self.tg_app: Optional[BaseProxy] = tg_app
        self._polling: bool = False
        self.offset: Optional[int] = None
        self.offset_start_date: Optional[datetime] = None
        self.offset_end_date: Optional[datetime] = None
        self.client: QiwiWrapper = client
        self._on_startup_calls: List[Callable] = []
        self._on_shutdown_calls: List[Callable] = []

        from glQiwiApi import QiwiWrapper
        QiwiWrapper.set_current(client)

    def __setitem__(self, key: str, callback: Callable):
        if key not in ["on_shutdown", "on_startup"]:
            raise RuntimeError()

        if not isinstance(callback, types.FunctionType):
            raise RuntimeError("Invalid type of callback")

        if key == "on_shutdown":
            self._on_shutdown_calls.append(callback)
        else:
            self._on_startup_calls.append(callback)

    async def _pre_process(self, get_updates_from: Optional[datetime]):
        """
        Preprocess method, which set start date and end date of polling
        :param get_updates_from: date from which will be polling
        """
        try:
            current_time = datetime.now()
            assert isinstance(get_updates_from, datetime)
            assert (
                           current_time - get_updates_from
                   ).total_seconds() > 0
        except AssertionError as ex:
            raise ValueError(
                "Invalid value of get_updates_from, it must "
                "be instance of datetime and no more than  the current time"
            ) from ex

        self.offset_end_date = current_time

        if self.offset_start_date is None:
            self.offset_start_date = get_updates_from
        else:
            self.offset_start_date = current_time - timedelta(milliseconds=1)

    async def _get_history(self) -> List[Transaction]:
        """
        Get history by call 'transactions' method from QiwiWrapper.
        If history is empty or not all transactions not isinstance
         class Transaction - raise exception

        """
        history = await self.client.transactions(
            end_date=self.offset_end_date,
            start_date=self.offset_start_date
        )

        if not history or not all(
                isinstance(txn, Transaction) for txn in history):
            raise NoUpdatesToExecute()

        return history

    async def _pool_process(
            self,
            get_updates_from: Optional[datetime]
    ):
        """
        Method, which manage pool process

        :param get_updates_from: date from which will be polling
        """
        await self._pre_process(get_updates_from)
        try:
            history: List[Transaction] = await self._get_history()
        except NoUpdatesToExecute:
            return

        last_payment: Transaction = history[0]
        last_txn_id: int = last_payment.transaction_id

        if self.offset is None:
            first_payment: Transaction = history[-1]
            self.offset = first_payment.transaction_id - 1

        await self._parse_history_and_process_events(
            history=history,
            last_payment_id=last_txn_id
        )

    async def _start_polling(self, **kwargs):
        """
        Blocking method, which start polling process

        :param kwargs:
        """
        self._polling = True
        timeout: float = parse_timeout(kwargs.pop("timeout"))
        while self._polling:
            try:
                await self._pool_process(**kwargs)
            except Exception as ex:
                self.dispatcher.logger.error("Handle `%s`. Set a smaller timeout or open issue. "
                                             "Sleeping %s seconds", repr(ex), timeout + 100)
                timeout += 100
            await asyncio.sleep(timeout)

    def _on_shutdown(self):
        """
        On shutdown, we gracefully cancel all tasks, close event loop
        and call `close` method to clear resources
        """
        coroutines: List[Coroutine] = [self.goodbye(), self.client.close()]
        if isinstance(self.tg_app, BaseProxy):
            coroutines.append(self._shutdown_tg_app())
        self._loop.run_until_complete(
            asyncio.gather(*coroutines, loop=self._loop)
        )

    async def _shutdown_tg_app(self):
        """
        Gracefully shutdown tg application

        """
        self.tg_app.dispatcher.stop_polling()
        await self.tg_app.dispatcher.storage.close()
        await self.tg_app.dispatcher.storage.wait_closed()
        await self.tg_app.dispatcher.bot.session.close()

    async def _parse_history_and_process_events(
            self,
            history: List[Transaction],
            last_payment_id: int
    ):
        """
        Processing events and send callbacks to handlers

        :param history: [list] list of :class:`Transaction`
        :param last_payment_id: id of last payment in history
        """
        history_iterator = iter(history[::-1])

        while self.offset < last_payment_id:
            try:
                payment = next(history_iterator)
                await self.dispatcher.process_event(payment)
                self.offset = payment.transaction_id
                self.offset_start_date = self.offset_end_date
            except StopIteration:  # handle exhausted iterator
                break

    def start_polling(
            self, *,
            get_updates_from: datetime = datetime.now(),
            timeout: Union[float, int, ClientTimeout] = DEFAULT_TIMEOUT,
            **kwargs
    ):
        try:
            self._loop.run_until_complete(self.welcome())
            self._loop.create_task(self._start_polling(
                get_updates_from=get_updates_from,
                timeout=timeout
            ))
            if isinstance(self.tg_app, BaseProxy):
                self.tg_app.setup(**kwargs, loop=self._loop)
            api_helper.run_forever_safe(loop=self._loop)
        except (SystemExit, KeyboardInterrupt):  # pragma: no cover
            # Allow to graceful shutdown
            pass
        finally:
            self._polling = False
            self._on_shutdown()

    def start_webhook(
            self, *,
            host: str = "localhost",
            port: int = 8080,
            path: Optional[Path] = None,
            app: Optional[web.Application] = None
    ):
        application = app or web.Application()

        hook_config, key = self._loop.run_until_complete(self.client.bind_webhook())

        server.setup(
            dispatcher=self.dispatcher,
            app=application,
            path=path,
            secret_key=self.client.secret_p2p,
            base64_key=key,
            tg_app=self.tg_app,
            host=host
        )

        try:
            self._loop.run_until_complete(self.welcome())
            web.run_app(application, host=host, port=port)
        except (KeyboardInterrupt, SystemExit):
            # Allow to graceful shutdown
            pass
        finally:
            self._on_shutdown()

    async def welcome(self) -> None:
        """ Execute on_startup callback"""
        self.dispatcher.logger.debug("Start polling!")
        for callback in self._on_startup_calls:
            await _inspect_and_execute_callback(
                callback=callback,
                client=self.client
            )

    async def goodbye(self) -> None:
        """ Execute on_shutdown callback """
        self.dispatcher.logger.debug("Goodbye!")
        for callback in self._on_shutdown_calls:
            await _inspect_and_execute_callback(
                callback=callback,
                client=self.client
            )
