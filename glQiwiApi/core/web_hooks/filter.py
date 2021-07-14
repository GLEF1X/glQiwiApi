from __future__ import annotations

import abc
import inspect
from typing import Any, Awaitable, cast

from .config import CF


class BaseFilter(abc.ABC):
    @abc.abstractmethod
    async def check(self, update: Any) -> bool:
        raise NotImplementedError

    def __and__(self, other: BaseFilter) -> AndFilter:
        if not isinstance(other, BaseFilter):
            raise TypeError(
                f"Can't compose two different types of filters, expected Filter, got {type(other)}"
            )
        return AndFilter(self, other)

    def __invert__(self) -> NotFilter:
        return NotFilter(self)


class AndFilter(BaseFilter):
    def __init__(self, filter1: BaseFilter, filter2: BaseFilter) -> None:
        self.filter2 = filter2
        self.filter1 = filter1

    async def check(self, update: Any) -> bool:
        return await self.filter1.check(update) and await self.filter2.check(update)


class NotFilter(BaseFilter):
    def __init__(self, filter_: BaseFilter):
        self.filter_ = filter_

    async def check(self, update: Any) -> bool:
        return not self.filter_.check(update)


class LambdaBasedFilter(BaseFilter):
    __name__: str

    def __init__(self, function: CF):
        self.__name__ = f"Filter around <{function!r}>"

        self.function: CF = function
        self.awaitable: bool = inspect.iscoroutinefunction(
            function
        ) or inspect.isawaitable(function)

    async def check(self, update: Any) -> bool:
        if self.awaitable:
            return await cast(Awaitable[bool], self.function(update))
        else:
            return cast(bool, self.function(update))


__all__ = ("LambdaBasedFilter", "BaseFilter")
