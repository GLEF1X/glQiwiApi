from __future__ import annotations

import abc
import inspect
from copy import deepcopy
from types import TracebackType
from typing import (
    TYPE_CHECKING as MYPY,
    Any,
    Optional,
    Type,
    TypeVar,
    Dict,
    Callable,
    Awaitable,
    Union,
)

if MYPY:
    from glQiwiApi.core.request_service import RequestServiceProto  # pragma: no cover

T = TypeVar("T", bound="BaseAPIClient")

RequestServiceFactoryType = Callable[
    ..., Union[Awaitable["RequestServiceProto"], "RequestServiceProto"]
]


class BaseAPIClient(abc.ABC):
    def __init__(
        self,
        request_service_factory: Optional[RequestServiceFactoryType] = None,
    ):
        self._request_service_factory = request_service_factory
        self._request_service: RequestServiceProto = None  # type: ignore

    async def __aenter__(self):  # type: ignore
        if self._request_service is None:
            self._request_service = await self.create_request_service()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def close(self) -> None:
        if self._request_service is None:
            return None

        await self._request_service.shutdown()

    async def create_request_service(self) -> RequestServiceProto:
        if self._request_service_factory is not None:
            if inspect.iscoroutinefunction(self._request_service_factory):
                return await self._request_service_factory(self)  # type: ignore
            return self._request_service_factory(self)  # type: ignore

        return await self._create_request_service()

    @abc.abstractmethod
    async def _create_request_service(self) -> RequestServiceProto:
        pass

    def __deepcopy__(self: T, memo: Dict[Any, Any]) -> T:
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            try:
                setattr(result, k, deepcopy(v, memo))
            except TypeError:
                pass
        return result
