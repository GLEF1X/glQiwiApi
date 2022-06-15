from __future__ import annotations

import abc
import asyncio
import inspect
import logging
import operator
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Iterable,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
)

from glQiwiApi.qiwi.clients.p2p.types import BillWebhook

from ...qiwi.clients.wallet.types.transaction import Transaction
from ...qiwi.clients.wallet.types.webhooks import TransactionWebhook
from .. import Handler
from .filters import BaseFilter, LambdaBasedFilter

logger = logging.getLogger('glQiwiApi.dispatcher')


class SkipHandler(Exception):
    pass


class CancelHandler(Exception):
    pass


Event = TypeVar('Event')
F = TypeVar('F', bound=Callable[..., Any])


class BaseDispatcher(abc.ABC):
    def __init__(self) -> None:
        self.exception_handler = HandlerCollection(Exception)

    async def process_event(self, event: Event, *args: Any) -> None:
        """
        Feed handlers with event.

        :param event: any object that will be propagated to handlers
        """
        coroutines = [h.notify(event, *args) for h in self.__all_handlers__]
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        for result in results:
            if self.exception_handler.is_empty:
                break
            if not isinstance(result, Exception):
                continue

            await self.exception_handler.notify(result, *args)

    @property
    @abc.abstractmethod
    def __all_handlers__(self) -> Sequence[HandlerCollection[Any]]:
        """Return all registered handlers except error handlers"""


class QiwiDispatcher(BaseDispatcher):
    def __init__(self) -> None:
        super().__init__()
        self.transaction_handler = HandlerCollection(Transaction, TransactionWebhook)
        self.bill_handler = HandlerCollection(BillWebhook)

    @property
    def __all_handlers__(self) -> Sequence[HandlerCollection[Any]]:
        return self.bill_handler, self.transaction_handler


class HandlerCollection(Generic[Event]):
    def __init__(self, *event_types: Type[Event], once: bool = True) -> None:
        self._handlers: List[EventHandler[Event]] = []
        self._once = once
        self._event_filter: Callable[[Event], bool] = lambda e: isinstance(e, event_types)

    async def notify(self, event: Event, *args: Any) -> None:
        if not self._event_filter(event):
            return None
        for handler in self._handlers:
            try:
                await handler.check_then_execute(event, *args)
                if self._once:
                    break
            except SkipHandler:
                continue
            except CancelHandler:
                break

    def __call__(self, *filters: BaseFilter[Event]) -> Callable[[F], F]:
        def decorator(callback: F) -> F:
            self.register_handler(callback, *filters)
            return callback

        return decorator

    def register_handler(
        self,
        event_handler: Union[Callable[..., Awaitable[Any]], Type[Handler[Event]]],
        *filters: Union[Callable[[Event], bool], BaseFilter[Event]],
    ) -> None:
        """
        Add new event handler.
        (!) Allows chain addition.

        :param event_handler: event handler, low order function
         which works with events
        :param filters: filter for low order function execution
        """
        generated_filters: List[BaseFilter[Event]] = []
        for filter_ in filters:
            if inspect.isfunction(filter_):
                generated_filters.append(LambdaBasedFilter(filter_))
            else:
                generated_filters.append(cast(BaseFilter[Event], filter_))

        self._handlers.append(EventHandler(event_handler, *generated_filters))

    def remove_handler(self, handler: EventHandler[Event]) -> None:
        self._handlers.remove(handler)

    def __iter__(self) -> Iterable[EventHandler[Event]]:
        return iter(self._handlers)

    @property
    def is_empty(self) -> bool:
        return len(self._handlers) == 0


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
        self._filters = tuple(filter(lambda f: operator.not_(operator.eq(f, None)), filters))

    async def check_then_execute(self, event: Event, *args: Any) -> Optional[Any]:
        """Check event, apply all filters and then pass on to handler"""
        for f in self._filters:
            if not await f.check(event):
                break
        else:
            return await self._handler(event, *args)
        return None  # hint for mypy
