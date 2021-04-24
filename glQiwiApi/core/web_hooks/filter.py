import inspect
import operator
from typing import Any, Callable

from glQiwiApi import types
from .config import CF, E


def op(a: CF, b: CF, event: Any) -> bool:
    """ custom a & b (and) operator """
    validated = a(event)
    if validated is not True:
        return False
    return operator.and_(validated, b(event))


def xor(a: CF, b: CF, event: Any) -> bool:
    """ custom a ^ b (xor) operator """
    funcs = (a, b)
    for func in funcs:
        if func(event):
            return True
    return False


def or_(a: CF, b: CF, event: Any) -> bool:
    """ Custom a | b (or) operator """
    return True if a(event) or b(event) else False


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
        return _compose_filter(self, other, xor)

    def __and__(self, other: "Filter") -> "Filter":
        return _compose_filter(self, other, op)

    def __or__(self, other: "Filter") -> "Filter":
        return _compose_filter(self, other, or_)


def _compose_filter(
        filter1: Filter,
        filter2: Filter,
        operator_: Any
) -> Filter:
    if (not isinstance(filter1, Filter)) | (not isinstance(filter2, Filter)):
        raise ValueError(
            f"Cannot compare non-Filter object with Filter, "
            f"got filter1={filter1.__name__} "
            f"operator={operator_.__name__} "
            f"filter2={filter2.__name__}"
        )

    func: CF

    if filter1.awaitable & filter2.awaitable:

        async def func(event: E) -> Any:
            return operator_(
                await filter1.function(event), await filter2.function(event)
            )

    elif filter1.awaitable ^ filter2.awaitable:
        is_f1_async = filter1.awaitable
        async_func = filter1 if is_f1_async else filter2
        sync_func = filter2 if is_f1_async else filter1

        async def func(event: E) -> Any:
            return operator_(
                await async_func.function(event), sync_func.function(event)
            )

    else:

        def func(event: E) -> Any:
            return operator_(filter1.function, filter2.function, event)

    return Filter(func)


def _sing_filter(filter1: Filter, operator_) -> Filter:
    func: CF

    if filter1.awaitable:

        async def func(event: E) -> Any:
            return operator_(await filter1.function(event))

    else:

        def func(event: E) -> Any:
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
