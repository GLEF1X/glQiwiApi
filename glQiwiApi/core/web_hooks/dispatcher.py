import asyncio
import inspect
import logging
import types
from datetime import datetime, timedelta
from typing import List, Tuple, Coroutine, Any, Union, Optional, NoReturn, \
    Callable

import aiohttp

from .config import EventHandlerFunctor, EventFilter, E
from .filter import Filter, transaction_webhook_filter, bill_webhook_filter


async def _inspect_and_execute_callback(client, callback: Callable):
    if inspect.iscoroutinefunction(callback):
        await callback(client)
    else:
        callback(client)


def _get_stream_handler() -> logging.StreamHandler:
    _log_format = f"%(asctime)s - [%(levelname)s] - %(message)s"
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(_log_format))
    return stream_handler


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)
    if not logger.handlers:
        logger.addHandler(_get_stream_handler())
    return logger


class EventHandler:
    """
    Event handler, which executing and working with handlers

    """

    def __init__(self, functor: EventHandlerFunctor, *filter_: Filter) -> None:
        """

        :param functor:
        :param filter_:
        """
        self._fn = functor
        self._filters = filter_

    async def check_then_execute(self, event: E) -> Coroutine[Any, Any, Any]:
        """
        Check event, apply all filters and than pass on to handler

        :param event: handler
        """
        for filter_ in self._filters:
            if filter_.awaitable:
                if not await filter_.function(event):
                    break
            else:
                if not filter_.function(event):
                    break
        else:
            return await self._fn(event)


class Dispatcher:
    """
    Class, which managing all handlers

    """

    def __init__(
            self,
            loop: asyncio.AbstractEventLoop,
            wallet: Any
    ):
        if not isinstance(loop, asyncio.AbstractEventLoop):
            raise ValueError(
                f"Listener must have its event loop implemented with"
                f" {asyncio.AbstractEventLoop!r}"
            )

        self.loop = loop
        self.transaction_handlers: List[EventHandler] = []
        self.bill_handlers: List[EventHandler] = []
        self._logger: logging.Logger = _setup_logger()
        # Polling variables
        self._polling: bool = False
        self.offset: Optional[int] = None
        self.offset_start_date: Optional[
            Union[
                datetime,
                timedelta
            ]
        ] = None
        self.offset_end_date = None
        self.client: Any = wallet
        self.request_timeout: Optional[
            Union[float, int, aiohttp.ClientTimeout]
        ] = None
        self._on_startup: List[Callable] = []
        self._on_shutdown: List[Callable] = []

    def register_transaction_handler(
            self,
            event_handler: EventHandlerFunctor,
            *filters: EventFilter
    ):
        self.transaction_handlers.append(
            self.wrap_handler(
                event_handler, filters,
                default_filter=transaction_webhook_filter
            )
        )

    def register_bill_handler(self, event_handler: EventHandlerFunctor,
                              *filters: EventFilter):
        self.bill_handlers.append(
            self.wrap_handler(
                event_handler, filters,
                default_filter=bill_webhook_filter
            )
        )

    @property
    def handlers(self) -> List[EventHandler]:
        """ Return all registered handlers """
        return [*self.bill_handlers, *self.transaction_handlers]

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @logger.setter
    def logger(self, logger: logging.Logger):
        self._logger = logger

    def __setitem__(self, key: str, callback: Callable):
        if key not in ["on_shutdown", "on_startup"]:
            raise ValueError()

        if not isinstance(callback, types.FunctionType):
            raise ValueError("Invalid type of callback")

        if key == "on_shutdown":
            self._on_shutdown.append(callback)
        else:
            self._on_startup.append(callback)

    @staticmethod
    def wrap_handler(
            event_handler: EventHandlerFunctor,
            filters: Tuple[Union[EventFilter, Filter], ...],
            default_filter: Filter
    ) -> EventHandler:
        """
        Add new event handler.
        (!) Allows chain addition.
        :param event_handler: event handler, low order function
         which works with events
        :param filters: filter for low order function execution
        :param default_filter: default filter for handler
        :return: this handler manager
        """
        if filters:  # Initially filters are in tuple
            filters_list = list(filters)

            for index, filter_ in enumerate(filters):
                if not isinstance(filter_, Filter):
                    filters_list[index] = default_filter & Filter(filter_)

            filters = tuple(filters_list)
        else:
            filters = (default_filter,)

        return EventHandler(event_handler, *filters)

    def transaction_handler_wrapper(self, *filters: EventFilter) -> E:

        def decorator(callback: EventHandlerFunctor) -> EventHandlerFunctor:
            self.register_transaction_handler(callback, *filters)
            return callback

        return decorator

    def bill_handler_wrapper(self, *filters: EventFilter) -> E:

        def decorator(callback: EventHandlerFunctor) -> EventHandlerFunctor:
            self.register_bill_handler(callback, *filters)
            return callback

        return decorator

    async def process_event(self, event: E) -> None:
        """
        Feed handlers with event.
        :param event: any object that will be translated to handlers
        """

        for handler in self.handlers:
            await handler.check_then_execute(event)

    async def welcome(self) -> None:
        """"""
        for callback in self._on_startup:
            await _inspect_and_execute_callback(
                callback=callback,
                client=self.client
            )

    async def goodbye(self) -> None:
        self.logger.info("Stop polling!")
        for callback in self._on_shutdown:
            await _inspect_and_execute_callback(
                callback=callback,
                client=self.client
            )
