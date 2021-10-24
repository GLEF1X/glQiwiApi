from __future__ import annotations

import asyncio
import functools
import logging
import operator
import types
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
    TypeVar,
    Type,
    Any,
    Iterable,
    no_type_check,
)

from glQiwiApi.builtin import (
    TransactionFilter,
    BillFilter,
    ErrorFilter,
)  # NOQA
from .class_based import (
    AbstractTransactionHandler,
    AbstractBillHandler,
    Handler,
    ErrorHandler,
)
from .filters import BaseFilter, LambdaBasedFilter
from ...builtin.logger import setup_logger

if TYPE_CHECKING:
    from glQiwiApi.types import Notification, WebHook, Transaction  # pragma: no cover
    from glQiwiApi.types.base import HashableBase, Base  # noqa  # pragma: no cover

Event = TypeVar("Event", bound=Union["HashableBase", Exception, "Base"])
_T = TypeVar("_T")
EventFilter = Callable[[Event], bool]
TxnFilters = Union[
    BaseFilter["Transaction"],
    BaseFilter["WebHook"],
    Callable[["WebHook"], bool],
    Callable[["Transaction"], bool],
]

BillFilters = Union[Callable[["Notification"], bool], BaseFilter["Notification"]]

HandlerType = TypeVar("HandlerType", bound="EventHandler[Any]")

# handlers
TxnRawHandler = Union[Type[AbstractTransactionHandler], Callable[..., Awaitable[Any]]]
BillRawHandler = Union[Type[AbstractBillHandler], Callable[..., Awaitable[Any]]]
ErrorRawHandler = Union[Type[ErrorHandler], Callable[..., Awaitable[Any]]]


class SkipHandler(Exception):
    pass


class CancelHandler(Exception):
    pass


class EventHandler(Generic[Event]):
    """
    Event handler, which executing and working with handlers

    """

    def __init__(
        self,
        handler: Union[Callable[..., Awaitable[Any]], Type[Handler[Event]]],
        *filters: BaseFilter[Event],
    ) -> None:
        self._handler = handler
        self._filters = list(
            filter(lambda f: operator.not_(operator.eq(f, None)), filters)
        )

    async def check_then_execute(self, event: Event, *args: Any) -> Optional[Any]:
        """Check event, apply all filters and then pass on to handler"""
        for f in self._filters:
            if not await f.check(event):
                break
        else:
            return await self._handler(event, *args)
        return None  # hint for mypy


TxnWrappedHandler = Union[EventHandler["Transaction"], EventHandler["WebHook"]]


class HandlerCollection(Generic[Event]):
    def __init__(self, once: bool = True) -> None:
        self.handlers: List[EventHandler[Event]] = []
        self.once = once

    async def notify(self, event: Event, *args: Any) -> None:
        for handler in self.handlers:
            try:
                await handler.check_then_execute(event, *args)
                if self.once:
                    break
            except SkipHandler:
                continue
            except CancelHandler:
                break

    def subscribe(self, handler: EventHandler[Event]) -> None:
        self.handlers.append(handler)

    def unsubscribe(self, handler: EventHandler[Event]) -> None:
        self.handlers.remove(handler)

    def __iter__(self) -> Iterable[EventHandler[Event]]:
        return iter(self.handlers)

    @property
    def is_empty(self) -> bool:
        return len(self.handlers) == 0


class Dispatcher:
    """
    Class, which managing all handlers

    """

    def __init__(self) -> None:
        self.transaction_handlers: HandlerCollection[
            Union["Transaction", "WebHook"]
        ] = HandlerCollection()
        self.bill_handlers: HandlerCollection["Notification"] = HandlerCollection()
        self.error_handlers: HandlerCollection[Exception] = HandlerCollection()
        self._logger = setup_logger()

    @no_type_check
    def _wrap_callback_for_error_handling(self, callback):
        @functools.wraps(callback)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await callback(*args, **kwargs)
            except (SkipHandler, CancelHandler) as ex:
                # reraise exception to handle it on HandlerCollection object and skip or break processing current event
                raise ex
            except Exception as e:
                if not self.error_handlers.is_empty:
                    return await self.error_handlers.notify(e, *args)
                raise e

        return wrapper

    def register_transaction_handler(
        self, event_handler: TxnRawHandler, *filters: TxnFilters
    ) -> None:
        self.transaction_handlers.subscribe(
            cast(  # type: ignore
                TxnWrappedHandler,
                self.wrap_handler(
                    self._wrap_callback_for_error_handling(event_handler),
                    filters,
                    default_filter=TransactionFilter(),
                ),
            )
        )

    def register_bill_handler(
        self, event_handler: BillRawHandler, *filters: BillFilters
    ) -> None:
        self.bill_handlers.subscribe(
            self.wrap_handler(
                self._wrap_callback_for_error_handling(event_handler),
                filters,
                default_filter=BillFilter(),
            )
        )

    def register_error_handler(
        self,
        event_handler: ErrorRawHandler,
        exception: Optional[Union[Type[Exception], Exception]] = None,
        *filters: BaseFilter[Exception],
    ) -> None:
        self.error_handlers.subscribe(
            self.wrap_handler(
                event_handler, filters=filters, default_filter=ErrorFilter(exception)
            )
        )

    @property
    def __all_handlers__(self):  # type: ignore
        """Return all registered handlers, except error handlers"""
        return self.bill_handlers, self.transaction_handlers

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
        event_handler: Union[Callable[..., Awaitable[Any]], Type[Handler[Event]]],
        filters: Optional[
            Tuple[Union[Callable[[Event], bool], BaseFilter[Event]], ...]
        ] = None,
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
        generated_filters: List[BaseFilter[Event]] = []
        if filters:
            for filter_ in filters:
                if isinstance(filter_, types.FunctionType):
                    generated_filters.append(LambdaBasedFilter(filter_))
                else:
                    generated_filters.append(cast(BaseFilter[Event], filter_))
            if default_filter is not None:
                generated_filters.insert(0, default_filter)
        else:
            generated_filters = [default_filter]  # type: ignore

        return EventHandler(event_handler, *generated_filters)

    def transaction_handler(
        self, *filters: TxnFilters
    ) -> Callable[[TxnRawHandler], TxnRawHandler]:
        def decorator(callback: TxnRawHandler) -> TxnRawHandler:
            self.register_transaction_handler(callback, *filters)
            return callback

        return decorator

    def bill_handler(
        self, *filters: BillFilters
    ) -> Callable[[BillRawHandler], BillRawHandler]:
        def decorator(callback: BillRawHandler) -> BillRawHandler:
            self.register_bill_handler(callback, *filters)
            return callback

        return decorator

    def error_handler(
        self,
        exception: Optional[Union[Type[Exception], Exception]] = None,
        *filters: BaseFilter[Exception],
    ) -> Callable[[ErrorRawHandler], ErrorRawHandler]:
        def decorator(callback: ErrorRawHandler) -> ErrorRawHandler:
            self.register_error_handler(callback, exception, *filters)
            return callback

        return decorator

    async def process_event(self, event: Event) -> None:
        """
        Feed handlers with event.

        :param event: any object that will be translated to handlers
        """
        coroutines = [
            handler_collection.notify(event=event)
            for handler_collection in self.__all_handlers__
        ]
        await asyncio.gather(*coroutines)
