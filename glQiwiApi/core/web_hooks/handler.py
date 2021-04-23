import asyncio
from typing import Any, Awaitable, Callable, List, Tuple, TypeVar

from .filter import Filter, transaction_webhook_filter, bill_webhook_filter

E = TypeVar("E")
EventFilter = Callable[[E], bool]
EventHandlerFunctor = Callable[[E], Awaitable[Any]]


class EventHandler:
    def __init__(self, functor: EventHandlerFunctor, *filter_: Filter):
        self._fn = functor
        self._filters = filter_

    async def check_then_execute(self, event: E):
        for filter_ in self._filters:
            if filter_.awaitable:
                if not await filter_.function(event):
                    break
            else:
                if not filter_.function(event):
                    break
        else:
            return await self._fn(event)


class HandlerManager:
    def __init__(
            self,
            loop: asyncio.AbstractEventLoop
    ):
        if not isinstance(loop, asyncio.AbstractEventLoop):
            raise ValueError(
                f"Listener must have its event loop implemented with"
                f" {asyncio.AbstractEventLoop!r}"
            )

        self.loop = loop
        self.transaction_handlers: List[EventHandler] = []
        self.bill_handlers: List[EventHandler] = []

    @property
    def _handlers(self) -> List[EventHandler]:
        return [*self.bill_handlers, *self.transaction_handlers]

    @staticmethod
    def wrap_handler(
            event_handler: EventHandlerFunctor,
            filters: Tuple[EventFilter, ...]
    ) -> EventHandler:
        """
        Add new event handler.
        (!) Allows chain addition.
        :param event_handler: event handler, low order function
         which works with events
        :param filters: filter for low order function execution
        :return: this handler manager
        """
        if filters:  # Initially filters are in tuple
            filters_list = list(filters)

            for index, filter_ in enumerate(filters):
                if not isinstance(filter_, Filter):
                    filters_list[index] = Filter(filter_)

            filters = tuple(filters_list)

        return EventHandler(event_handler, *filters)

    def add_transaction_handler(self, *filters: EventFilter) -> E:

        def decorator(event_handler: EventHandlerFunctor) -> None:
            with_default = add_filter(filters, transaction_webhook_filter)
            handler = self.wrap_handler(event_handler, with_default)
            self.transaction_handlers.append(handler)

        return decorator

    def add_bill_handler(self, *filters: EventFilter) -> E:

        def decorator(event_handler: EventHandlerFunctor) -> None:
            with_default = add_filter(filters, bill_webhook_filter)
            handler = self.wrap_handler(event_handler, with_default)
            self.bill_handlers.append(handler)

        return decorator

    async def process_event(self, event: E) -> None:
        """
        Feed handlers with event.
        :param event: any object that will be translated to handlers
        """

        for handler in self._handlers:
            await handler.check_then_execute(event)


def add_filter(
        filters: Tuple[E, ...],
        custom_filter: Filter
) -> Tuple[E, ...]:
    """
    Added default filter for different handlers

    :param filters: current filters
    :param custom_filter: filter, which you want to append
    """
    filters = list(filters)
    filters.append(custom_filter.function)
    return tuple(filters)
