from __future__ import annotations

import abc
from copy import deepcopy
from types import TracebackType
from typing import TYPE_CHECKING, Any, Optional, Type, TypeVar, Dict

from glQiwiApi.core.cache.storage import CacheStorage

if TYPE_CHECKING:
    from glQiwiApi.core.request_service import RequestServiceProto  # pragma: no cover

W = TypeVar("W", bound="BaseAPIClient")


class BaseAPIClient(abc.ABC):
    def __init__(
        self,
        request_service: Optional[RequestServiceProto] = None,
        cache_storage: Optional[CacheStorage] = None,
    ):
        self._cache_storage = cache_storage
        self._request_service: RequestServiceProto = (
            request_service or self._create_request_service()
        )

    @abc.abstractmethod
    def _create_request_service(self) -> RequestServiceProto:
        pass

    async def __aenter__(self):  # type: ignore
        await self._request_service.warmup()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self._request_service.shutdown()

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
