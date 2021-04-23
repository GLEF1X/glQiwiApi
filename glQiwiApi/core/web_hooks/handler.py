import asyncio
from typing import Any, Awaitable, Callable, List, Tuple, TypeVar

from .filter import Filter

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
        self._event_handlers: List[EventHandler] = []

    def add_event_handler(
            self,
            event_handler: EventHandlerFunctor,
            filters: Tuple[EventFilter, ...]
    ) -> 'HandlerManager':
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

        self._event_handlers.append(EventHandler(event_handler, *filters))

        return self

    def __call__(self, *filter_: EventFilter):
        """
        Listener is callable for registering new event handlers
        :param filter_: Filter objects unpacked
        """

        def decorator(event_handler: EventHandlerFunctor) -> None:
            self.add_event_handler(event_handler, filter_)

        return decorator

    async def process_event(self, event: E) -> None:
        """
        Feed handlers with event.
        :param event: any object that will be translated to handlers
        """

        for handler in self._event_handlers:
            await handler.check_then_execute(event)
