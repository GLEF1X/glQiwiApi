from __future__ import annotations

import abc
import inspect
from typing import Any, Awaitable, cast, Generic, TypeVar, Callable, Union

_T = TypeVar("_T")


class BaseFilter(abc.ABC, Generic[_T]):
    @abc.abstractmethod
    async def check(self, update: _T) -> bool:
        raise NotImplementedError

    def __and__(self, other: BaseFilter[_T]) -> AndFilter[_T]:
        if not isinstance(other, BaseFilter):
            raise TypeError(
                f"Can't compose two different types of filters, expected Filter, got {type(other)}"
            )
        return AndFilter(self, other)

    def __invert__(self) -> NotFilter[_T]:
        return NotFilter(self)


class AndFilter(BaseFilter[_T]):
    def __init__(self, filter1: BaseFilter[_T], filter2: BaseFilter[_T]) -> None:
        self.filter2 = filter2
        self.filter1 = filter1

    async def check(self, update: Any) -> bool:
        return await self.filter1.check(update) and await self.filter2.check(update)


class NotFilter(BaseFilter[_T]):
    def __init__(self, filter_: BaseFilter[_T]):
        self.filter_ = filter_

    async def check(self, update: _T) -> bool:
        return not self.filter_.check(update)


class LambdaBasedFilter(BaseFilter[_T]):
    __name__: str

    def __init__(self, function: Callable[[_T], Union[bool, Awaitable[bool]]]) -> None:
        self.__name__ = f"Filter around <{function!r}>"

        self.function = function
        self.awaitable: bool = inspect.iscoroutinefunction(
            function
        ) or inspect.isawaitable(function)

    async def check(self, update: _T) -> bool:
        if self.awaitable:
            return await cast(Awaitable[bool], self.function(update))
        else:
            return cast(bool, self.function(update))


__all__ = ("LambdaBasedFilter", "BaseFilter")
