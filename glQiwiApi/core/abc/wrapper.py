from __future__ import annotations

import abc
from copy import deepcopy
from types import TracebackType
from typing import TYPE_CHECKING, Any, Optional, Type, TypeVar, Dict

if TYPE_CHECKING:
    from glQiwiApi.core.request_service import RequestService  # pragma: no cover

W = TypeVar("W", bound="Wrapper")


class Wrapper(abc.ABC):
    __slots__ = ()

    async def __aenter__(self):  # type: ignore
        await self.get_request_service().warmup()
        return self

    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_value: Optional[BaseException],
            traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self.get_request_service().shutdown()

    @abc.abstractmethod
    def get_request_service(self) -> RequestService:
        pass

    def __deepcopy__(self: W, memo: Dict[Any, Any]) -> W:
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            try:
                setattr(result, k, deepcopy(v, memo))
            except TypeError:
                pass
        return result
