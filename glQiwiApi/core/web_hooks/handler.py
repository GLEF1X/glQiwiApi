import asyncio
from typing import List, Tuple, Coroutine

from .config import EventHandlerFunctor, EventFilter, E
from .filter import Filter, transaction_webhook_filter, bill_webhook_filter


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

    async def check_then_execute(self, event: E) -> Coroutine:
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


class HandlerManager:
    """
    Manager, which managing all handlers

    """

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
    def handlers(self) -> List[EventHandler]:
        """ Return all registered handlers """
        return [*self.bill_handlers, *self.transaction_handlers]

    @staticmethod
    def wrap_handler(
            event_handler: EventHandlerFunctor,
            filters: Tuple[EventFilter, ...],
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

    def add_transaction_handler(self, *filters: EventFilter) -> E:

        def decorator(event_handler: EventHandlerFunctor) -> None:
            self.transaction_handlers.append(
                self.wrap_handler(
                    event_handler, filters,
                    default_filter=transaction_webhook_filter
                )
            )

        return decorator

    def add_bill_handler(self, *filters: EventFilter) -> E:

        def decorator(event_handler: EventHandlerFunctor) -> None:
            self.bill_handlers.append(
                self.wrap_handler(
                    event_handler, filters,
                    default_filter=bill_webhook_filter
                )
            )

        return decorator

    async def process_event(self, event: E) -> None:
        """
        Feed handlers with event.
        :param event: any object that will be translated to handlers
        """

        for handler in self.handlers:
            await handler.check_then_execute(event)
