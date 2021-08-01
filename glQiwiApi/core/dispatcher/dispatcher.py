from __future__ import annotations

import asyncio
import logging
import types
from itertools import chain, filterfalse
from typing import (
    List,
    Tuple,
    Callable,
    Union,
    Awaitable,
    Optional,
    cast,
    Generic,
    TYPE_CHECKING,
    Iterator,
    TypeVar, Type, Any,
)

from .class_based import AbstractTransactionHandler, AbstractBillHandler, Handler
from .filters import BaseFilter, LambdaBasedFilter
from ..builtin import TransactionFilter, BillFilter, InterceptHandler  # NOQA

if TYPE_CHECKING:
    from glQiwiApi.types import Notification, WebHook, Transaction  # NOQA
    from glQiwiApi.types.base import Base  # noqa

Event = TypeVar("Event", bound="Base")  # for events that come from api such as Transaction, WebHook or Notification
_T = TypeVar("_T")
EventFilter = Callable[[Event], bool]
TxnRawHandler = Union[Callable[["WebHook"], Awaitable[Any]], Callable[["Transaction"], Awaitable[Any]],
                      Type[AbstractTransactionHandler]]
TxnFilters = Union[
    BaseFilter["Transaction"],
    BaseFilter["WebHook"],
    Callable[["WebHook"], bool],
    Callable[["Transaction"], bool],
]

BillRawHandler = Union[Callable[["Notification"], Awaitable[Any]], Type[AbstractBillHandler]]
BillFilters = Union[Callable[["Notification"], bool], BaseFilter["Notification"]]


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    aiohttp_logger = logging.getLogger('aiohttp.access')
    logger.setLevel(level=logging.DEBUG)
    aiohttp_logger.setLevel(level=logging.DEBUG)
    if not logger.handlers:
        logger.addHandler(InterceptHandler())
        aiohttp_logger.addHandler(InterceptHandler())
    return logger


# It's highly undesirable to use this object outside the module, because this can lead to incorrect work
_update_handled = asyncio.Event()


class EventHandler(Generic[Event]):
    """
    Event handler, which executing and working with handlers

    """

    def __init__(self, handler: Union[Callable[[Event], Awaitable[Any]], Type[Handler[Event]]],
                 *filters: Optional[BaseFilter[Event]]) -> None:
        self._handler = handler
        self._filters: List[BaseFilter[Event]] = list(filterfalse(lambda f: f is not None, filters))  # type: ignore

    async def check_then_execute(self, event: Event) -> Optional[Any]:
        """Check event, apply all filters and then pass on to handler"""
        if _update_handled.is_set():
            return None

        for filter_ in self._filters:
            if not await filter_.check(event):
                break
        else:
            async with asyncio.Lock():
                _update_handled.set()
            return await self._handler(event)
        return None  # hint for mypy


TxnWrappedHandler = Union[EventHandler["Transaction"], EventHandler["WebHook"]]


class Dispatcher:
    """
    Class, which managing all handlers

    """

    def __init__(self) -> None:
        self.transaction_handlers: List[TxnWrappedHandler] = []
        self.bill_handlers: List[EventHandler["Notification"]] = []
        self._logger = _setup_logger()

    def register_transaction_handler(self, event_handler: TxnRawHandler, *filters: TxnFilters) -> None:
        self.transaction_handlers.append(
            cast(
                TxnWrappedHandler,
                self.wrap_handler(event_handler, filters, default_filter=TransactionFilter()),
            )
        )

    def register_bill_handler(self, event_handler: BillRawHandler, *filters: BillFilters) -> None:
        self.bill_handlers.append(self.wrap_handler(event_handler, filters, default_filter=BillFilter()))

    @property
    def handlers(self) -> Iterator[Union[TxnWrappedHandler, EventHandler["Notification"]]]:
        """Return all registered handlers"""
        return chain(self.bill_handlers, self.transaction_handlers)

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
            event_handler: Union[Callable[[Event], Awaitable[_T]], Type[Handler[Event]]],
            filters: Tuple[Union[Callable[[Event], bool], BaseFilter[Event]], ...],
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
        if filters:
            for filter_ in filters:
                if isinstance(filter_, types.FunctionType):
                    generated_filters.append(LambdaBasedFilter(filter_))
                else:
                    generated_filters.append(cast(BaseFilter[Event], filter_))
            generated_filters.insert(0, default_filter)
        else:
            generated_filters = [default_filter]

        return EventHandler(event_handler, *generated_filters)

    def transaction_handler_wrapper(self, *filters: TxnFilters) -> Callable[[TxnRawHandler], TxnRawHandler]:
        def decorator(callback: TxnRawHandler) -> TxnRawHandler:
            self.register_transaction_handler(callback, *filters)
            return callback

        return decorator

    def bill_handler_wrapper(self, *filters: BillFilters) -> Callable[[BillRawHandler], BillRawHandler]:
        def decorator(callback: BillRawHandler) -> BillRawHandler:
            self.register_bill_handler(callback, *filters)
            return callback

        return decorator

    async def feed_event(self, event: Event) -> None:
        """
        Feed handlers with event.

        :param event: any object that will be translated to handlers
        """
        tasks = [
            asyncio.create_task(handler.check_then_execute(event))  # type: ignore
            for handler in self.handlers
        ]
        try:
            await asyncio.gather(*tasks)
        finally:
            _update_handled.clear()
