from __future__ import annotations

import abc
import inspect
from typing import Any, Awaitable, Callable, Generic, Tuple, Type, TypeVar, Union, cast

Event = TypeVar('Event')


class BaseFilter(abc.ABC, Generic[Event]):
    @abc.abstractmethod
    async def check(self, update: Event) -> bool:
        raise NotImplementedError

    def __and__(self, other: BaseFilter[Event]) -> AndFilter[Event]:
        if not isinstance(other, BaseFilter):
            raise TypeError(
                f"Can't compose two different types of filters, expected Filter, got {type(other)}"
            )
        return AndFilter(self, other)

    def __invert__(self) -> NotFilter[Event]:
        return NotFilter(self)


class AndFilter(BaseFilter[Event]):
    def __init__(self, filter1: BaseFilter[Event], filter2: BaseFilter[Event]) -> None:
        self.filter2 = filter2
        self.filter1 = filter1

    async def check(self, update: Any) -> bool:
        return await self.filter1.check(update) and await self.filter2.check(update)


class NotFilter(BaseFilter[Event]):
    def __init__(self, filter_: BaseFilter[Event]):
        self.filter_ = filter_

    async def check(self, update: Event) -> bool:
        return not await self.filter_.check(update)


class LambdaBasedFilter(BaseFilter[Event]):
    def __init__(self, func: Callable[[Event], Union[bool, Awaitable[bool]]]) -> None:
        self.name = f'Filter around <{func!r}>'

        self.function = func
        self.awaitable: bool = inspect.iscoroutinefunction(func) or inspect.isawaitable(func)

    async def check(self, update: Event) -> bool:
        if self.awaitable:
            return await cast(Awaitable[bool], self.function(update))
        else:
            return cast(bool, self.function(update))


class ExceptionFilter(BaseFilter[Event]):
    def __init__(self, exception: Union[Type[Exception], Tuple[Type[Exception]]]):
        self._exception = exception

    async def check(self, update: Event) -> bool:
        return isinstance(update, self._exception)


__all__ = ('LambdaBasedFilter', 'BaseFilter', 'NotFilter', 'AndFilter', 'Event', 'ExceptionFilter')
