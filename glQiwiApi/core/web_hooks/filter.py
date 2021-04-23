import inspect
import operator
from typing import Any, Awaitable, Callable, TypeVar, Union

from glQiwiApi import types

E = TypeVar("E")
CF = Callable[[E], Union[Awaitable[bool], bool]]


class Filter:
    """
    Base Filter object, callback container
    Same approach used in https://github.com/uwinx/garnet
    """

    __name__: str

    def __init__(self, function: CF):
        self.__name__ = f"Filter around <{function!r}>"

        self.function: Callable = function
        self.awaitable: bool = inspect.iscoroutinefunction(
            function
        ) or inspect.isawaitable(function)

    def __eq__(self, other: Any) -> "Filter":
        return _sing_filter(self, lambda filter1: operator.eq(filter1, other))

    def __ne__(self, other: Any) -> "Filter":
        return _sing_filter(self, lambda filter1: operator.ne(filter1, other))

    def __invert__(self) -> "Filter":
        return _sing_filter(self, operator.not_)

    def __xor__(self, other: "Filter") -> "Filter":
        return _compose_filter(self, other, operator.xor)

    def __and__(self, other: "Filter") -> "Filter":
        return _compose_filter(self, other, operator.and_)

    def __or__(self, other: "Filter") -> "Filter":
        return _compose_filter(self, other, operator.or_)


def _compose_filter(filter1: Filter, filter2: Filter, operator_) -> Filter:
    if (not isinstance(filter1, Filter)) | (not isinstance(filter2, Filter)):
        raise ValueError(
            f"Cannot compare non-Filter object with Filter, "
            f"got filter1={filter1.__name__} "
            f"operator={operator_.__name__} "
            f"filter2={filter2.__name__}"
        )

    func: CF

    if filter1.awaitable & filter2.awaitable:

        async def func(event: E):
            return operator_(
                await filter1.function(event), await filter2.function(event)
            )

    elif filter1.awaitable ^ filter2.awaitable:
        is_f1_async = filter1.awaitable
        async_func = filter1 if is_f1_async else filter2
        sync_func = filter2 if is_f1_async else filter1

        async def func(event: E):
            return operator_(
                await async_func.function(event), sync_func.function(event)
            )

    else:

        def func(event: E):
            return operator_(filter1.function(event), filter2.function(event))

    return Filter(func)


def _sing_filter(filter1: Filter, operator_) -> Filter:
    func: CF

    if filter1.awaitable:

        async def func(event: E):
            return operator_(await filter1.function(event))

    else:

        def func(event: E):
            return operator_(filter1.function(event))

    return Filter(func)


transaction_webhook_filter = Filter(
    lambda update: isinstance(update, types.WebHook)
)

bill_webhook_filter = Filter(
    lambda update: isinstance(update, types.Notification)
)

__all__ = (
    "Filter",
    "transaction_webhook_filter",
    "bill_webhook_filter"
)
