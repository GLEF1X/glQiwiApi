from __future__ import annotations

import asyncio
import logging
import types
from itertools import chain
from typing import List, Tuple, Callable, Union, TypeVar, Awaitable, Optional, cast, Any, Generic, TYPE_CHECKING, \
    Iterator

from .filter import BaseFilter, LambdaBasedFilter
from ..builtin import TransactionFilter, BillFilter, InterceptHandler  # NOQA

if TYPE_CHECKING:
    from glQiwiApi.types import WebHook, Notification, Transaction


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)
    if not logger.handlers:
        logger.addHandler(InterceptHandler())
    return logger


Event = TypeVar("Event")  # for events that come from api such as Transaction, WebHook or Notification
_T = TypeVar("_T")
EventFilter = Callable[[Event], bool]


class StopHandlingOtherTasks(Exception):
    ...


# It's highly undesirable to use this object outside the module, as this can lead to incorrect work
_update_handled = asyncio.Event()


class EventHandler(Generic[Event]):
    """
    Event handler, which executing and working with handlers

    """

    def __init__(self, handler: Callable[[Event], Awaitable[_T]], *filters: Optional[BaseFilter[Event]]) -> None:
        """

        :param functor:
        :param filters:
        """
        self._handler = handler
        self._filters: List[BaseFilter[Event]] = [filter_ for filter_ in filters if filter_ is not None]

    async def check_then_execute(self, event: Event) -> Optional[_T]:
        """Check event, apply all filters and than pass on to handler"""
        if _update_handled.is_set():
            return None

        for filter_ in self._filters:
            if not await filter_.check(event):
                break
        else:
            async with asyncio.Lock():
                _update_handled.set()
            return await self._handler(event)

        return None


class Dispatcher:
    """
    Class, which managing all handlers

    """

    def __init__(self) -> None:
        self.transaction_handlers: List[Union[EventHandler["WebHook"], EventHandler["Transaction"]]] = []
        self.bill_handlers: List[EventHandler["Notification"]] = []
        self._logger = _setup_logger()

    def register_transaction_handler(
            self,
            event_handler: Union[Callable[["WebHook"], Awaitable[_T]], Callable[["Transaction"], Awaitable[_T]]],
            *filters: Union[BaseFilter["Transaction"], BaseFilter["WebHook"], Callable[["WebHook"], bool],
                            Callable[["Transaction"], bool]],
    ) -> None:
        self.transaction_handlers.append(
            cast(
                Union[EventHandler["Transaction"], EventHandler["WebHook"]],
                self.wrap_handler(event_handler, filters, default_filter=TransactionFilter())
            )
        )

    def register_bill_handler(
            self,
            event_handler: Callable[["Notification"], Awaitable[_T]],
            *filters: Union[Callable[["Notification"], bool], BaseFilter["Notification"]],
    ) -> None:
        self.bill_handlers.append(self.wrap_handler(event_handler, filters, default_filter=BillFilter()))

    @property
    def handlers(self) -> Iterator[Union[EventHandler["WebHook"],
                                         EventHandler["Transaction"],
                                         EventHandler["Notification"]]]:
        """Return all registered handlers"""
        gen = (handler for handler in chain(self.bill_handlers, self.transaction_handlers))
        return cast(Iterator[Union[EventHandler["WebHook"],
                                   EventHandler["Transaction"],
                                   EventHandler["Notification"]]], gen)

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @logger.setter
    def logger(self, logger: logging.Logger) -> None:
        if not isinstance(logger, logging.Logger):
            raise TypeError(f"Expected Logger instance, instead got {logger}.")
        self._logger = logger

    @staticmethod
    def wrap_handler(
            event_handler: Callable[[Event], Awaitable[_T]],
            filters: Tuple[Union[Callable[[Any], bool], BaseFilter[Event]], ...],
            default_filter: Optional[BaseFilter[Event]] = None,
    ) -> EventHandler[Event]:
        """
        Add new event handler.
        (!) Allows chain addition.

        :param event_handler: event handler, low order function
         which works with events
        :param filters: filter for low order function execution
        :param default_filter: default filter for the handler to determine type
         of update and accurately split handlers by the type of update

        :return: instance of EventHandler
        """
        generated_filters: List[Optional[BaseFilter[Event]]] = []
        if filters:  # Initially filters are in tuple
            for index, filter_ in enumerate(filters):
                if isinstance(filter_, types.FunctionType):
                    generated_filters.append(LambdaBasedFilter(filter_))
                else:
                    generated_filters.append(cast(BaseFilter[Event], filter_))
            generated_filters.insert(0, default_filter)
        else:
            generated_filters = [default_filter]

        return EventHandler(event_handler, *generated_filters)

    def transaction_handler_wrapper(
            self, *filters: Union[Callable[[Any], bool], BaseFilter["WebHook"], BaseFilter["Transaction"]]
    ) -> Callable[[Callable[[Union["WebHook", "Transaction"]], Awaitable[_T]]],
                  Callable[[Union["WebHook", "Transaction"]], Awaitable[_T]]]:

        def decorator(callback: Callable[[Union["WebHook", "Transaction"]],
                                         Awaitable[_T]]) -> Callable[[Union["WebHook", "Transaction"]], Awaitable[_T]]:
            self.register_transaction_handler(callback, *filters)
            return callback

        return decorator

    def bill_handler_wrapper(
            self, *filters: Union[Callable[[Any], bool], BaseFilter["Notification"]]
    ) -> Callable[[Callable[["Notification"], Awaitable[_T]]], Callable[["Notification"], Awaitable[_T]]]:
        def decorator(callback: Callable[["Notification"], Awaitable[_T]]) -> Callable[["Notification"], Awaitable[_T]]:
            self.register_bill_handler(callback, *filters)
            return callback

        return decorator

    async def process_event(self, event: Union["WebHook", "Notification", "Transaction"]) -> None:
        """
        Feed handlers with event.
        :param event: any object that will be translated to handlers
        """
        tasks = []
        for handler in self.handlers:
            tasks.append(asyncio.create_task(handler.check_then_execute(event)))  # type: ignore

        await asyncio.gather(*tasks)
        _update_handled.clear()
