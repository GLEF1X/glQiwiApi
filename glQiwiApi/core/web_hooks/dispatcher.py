import logging
import types
from typing import List, Tuple, Callable, Union

from .config import EventHandlerFunctor, EventFilter, E
from .filter import BaseFilter, LambdaBasedFilter
from ..builtin import bill_webhook_filter, transaction_webhook_filter, InterceptHandler  # NOQA


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)
    if not logger.handlers:
        logger.addHandler(InterceptHandler())
    return logger


HandlerAlias = Callable[[EventHandlerFunctor], EventHandlerFunctor]


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

    async def check_then_execute(self, event: E):
        """
        Check event, apply all filters and than pass on to handler

        :param event: handler
        """
        for filter_ in self._filters:
            if not await filter_.check(event):
                break
        else:
            return await self._fn(event)


class Dispatcher:
    """
    Class, which managing all handlers

    """

    def __init__(self) -> None:
        self.transaction_handlers: List[EventHandler] = []
        self.bill_handlers: List[EventHandler] = []
        self._logger = _setup_logger()

    def register_transaction_handler(self, event_handler: EventHandlerFunctor, *filters: EventFilter) -> None:
        self.transaction_handlers.append(
            self.wrap_handler(
                event_handler, filters, default_filter=transaction_webhook_filter
            )
        )

    def register_bill_handler(self, event_handler: EventHandlerFunctor, *filters: EventFilter) -> None:
        self.bill_handlers.append(
            self.wrap_handler(
                event_handler, filters, default_filter=bill_webhook_filter
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

    @staticmethod
    def wrap_handler(
            event_handler: EventHandlerFunctor,
            filters: Tuple[EventFilter, ...],
            default_filter: LambdaBasedFilter,
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
        generated_filters = []
        if filters:  # Initially filters are in tuple
            for index, filter_ in enumerate(filters):
                if isinstance(filter_, types.FunctionType):
                    generated_filters.append(LambdaBasedFilter(filter_))
                else:
                    generated_filters.append(filter_)
            generated_filters.insert(0, default_filter)
        else:
            generated_filters = [default_filter]

        return EventHandler(event_handler, *generated_filters)

    def transaction_handler_wrapper(self, *filters: Union[EventFilter, BaseFilter]) -> HandlerAlias:
        def decorator(callback: EventHandlerFunctor) -> EventHandlerFunctor:
            self.register_transaction_handler(callback, *filters)
            return callback

        return decorator

    def bill_handler_wrapper(self, *filters: Union[EventFilter, BaseFilter]) -> HandlerAlias:
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
