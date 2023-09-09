from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Dict, Generic, TypeVar, Union

if TYPE_CHECKING:
    from glQiwiApi.types.base import Base  # NOQA # pragma: no cover

T = TypeVar('T', bound=Union[Exception, 'Base'])


class BaseHandlerMixin(Generic[T]):
    if TYPE_CHECKING:  # pragma: no cover
        event: T


class Handler(abc.ABC, BaseHandlerMixin[T]):
    """Base class for all class-based handlers"""

    def __init__(self, event: T, *args: Any) -> None:
        self.event: T = event
        self._args = args
        if args:
            self.context: Dict[str, Any] = args[0].context

    @abc.abstractmethod
    async def process_event(self) -> Any:  # pragma: no cover  # type: ignore
        raise NotImplementedError

    def __await__(self) -> Any:
        return self.process_event().__await__()
