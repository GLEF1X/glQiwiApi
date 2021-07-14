import asyncio
import logging
import types
from typing import List, Tuple, Callable, Union, TypeVar, Awaitable, Optional, cast

from .filter import BaseFilter, LambdaBasedFilter
from ..builtin import TransactionFilter, BillFilter, InterceptHandler  # NOQA


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)
    if not logger.handlers:
        logger.addHandler(InterceptHandler())
    return logger


E = TypeVar("E")
_T = TypeVar("_T")
EventFilter = Callable[[E], bool]
EventHandlerFunctor = Callable[[E], Awaitable[_T]]
HandlerAlias = Callable[[EventHandlerFunctor], EventHandlerFunctor]


class StopHandlingOtherTasks(Exception):
    ...


# It's highly undesirable to use this object outside the module, as this can lead to incorrect work
_update_handled = asyncio.Event()


class EventHandler:
    """
    Event handler, which executing and working with handlers

    """

    def __init__(self, functor: EventHandlerFunctor, *filters: BaseFilter) -> None:
        """

        :param functor:
        :param filters:
        """
        self._fn = functor
        self._filters = filters

    async def check_then_execute(self, event: E) -> Optional[_T]:
        """Check event, apply all filters and than pass on to handler"""
        if _update_handled.is_set():
            return None

        for filter_ in self._filters:
            if not await filter_.check(event):
                break
        else:
            async with asyncio.Lock():
                _update_handled.set()
            await self._fn(event)

        return None  # hint for mypy(missing return statement)


class Dispatcher:
    """
    Class, which managing all handlers

    """

    def __init__(self) -> None:
        self.transaction_handlers: List[EventHandler] = []
        self.bill_handlers: List[EventHandler] = []
        self._logger = _setup_logger()
        self._once = False

    def register_transaction_handler(
        self,
        event_handler: EventHandlerFunctor,
        *filters: Union[BaseFilter, EventFilter],
    ) -> None:
        self.transaction_handlers.append(
            self.wrap_handler(
                event_handler, filters, default_filter=TransactionFilter()
            )
        )

    def register_bill_handler(
        self,
        event_handler: EventHandlerFunctor,
        *filters: Union[EventFilter, BaseFilter],
    ) -> None:
        self.bill_handlers.append(
            self.wrap_handler(event_handler, filters, default_filter=BillFilter())
        )

    @property
    def handlers(self) -> List[EventHandler]:
        """ Return all registered handlers """
        return [*self.bill_handlers, *self.transaction_handlers]

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
        event_handler: EventHandlerFunctor,
        filters: Tuple[Union[EventFilter, BaseFilter], ...],
        default_filter: BaseFilter,
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
        generated_filters: List[BaseFilter] = []
        if filters:  # Initially filters are in tuple
            for index, filter_ in enumerate(filters):
                if isinstance(filter_, types.FunctionType):
                    generated_filters.append(LambdaBasedFilter(filter_))
                else:
                    generated_filters.append(cast(BaseFilter, filter_))
            generated_filters.insert(0, default_filter)
        else:
            generated_filters = [default_filter]

        return EventHandler(event_handler, *generated_filters)

    def transaction_handler_wrapper(
        self, *filters: Union[EventFilter, BaseFilter]
    ) -> HandlerAlias:
        def decorator(callback: EventHandlerFunctor) -> EventHandlerFunctor:
            self.register_transaction_handler(callback, *filters)
            return callback

        return decorator

    def bill_handler_wrapper(
        self, *filters: Union[EventFilter, BaseFilter]
    ) -> HandlerAlias:
        def decorator(callback: EventHandlerFunctor) -> EventHandlerFunctor:
            self.register_bill_handler(callback, *filters)
            return callback

        return decorator

    async def process_event(self, event: E) -> None:
        """
        Feed handlers with event.
        :param event: any object that will be translated to handlers
        """
        tasks = []
        for handler in self.handlers:
            tasks.append(asyncio.create_task(handler.check_then_execute(event)))

        await asyncio.gather(*tasks)
        _update_handled.clear()
