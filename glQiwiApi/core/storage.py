from __future__ import annotations

import abc
import asyncio
import http
import time
from asyncio import Task
from dataclasses import dataclass
from typing import Any, Optional, Dict, Union, Tuple, List

UNCACHED = ("https://api.qiwi.com/partner/bill", "/sinap/api/v2/terms/")

INFINITE = float("inf")

ADD_TIME_PLACEHOLDER = "add_time"
VALUE_PLACEHOLDER = "value"


class CacheExpired(Exception):
    pass


class ContainsNonCacheable(Exception):
    pass


def _embed_cache_time(**kwargs: Any) -> Dict[Any, Any]:
    return {
        key: {
            VALUE_PLACEHOLDER: value,
            ADD_TIME_PLACEHOLDER: time.monotonic()
        }
        for key, value in kwargs.items()
    }


class Payload:

    def __init__(self, headers: Optional[Dict[Any, Any]] = None,
                 json: Optional[Dict[Any, Any]] = None,
                 params: Optional[Dict[Any, Any]] = None,
                 data: Optional[Dict[Any, Any]] = None, **kwargs: Any) -> None:
        self.headers = headers
        self.json = json
        self.params = params
        self.data = data

    @classmethod
    def new(cls, kwargs: Dict[Any, Any], args: Tuple[Any, ...]) -> Payload:
        return cls(
            **{k: kwargs.get(k) for k in args if isinstance(kwargs.get(k), dict)}
        )


@dataclass(frozen=True)
class CachedAPIRequest:
    payload: Payload
    response: Any
    method: Union[str, http.HTTPStatus]


class CacheInvalidationStrategy(abc.ABC):

    @abc.abstractmethod
    def process_update(self, **kwargs: Any) -> None:
        pass

    def process_delete(self) -> None:
        pass

    @abc.abstractmethod
    def process_retrieve(self, **kwargs: Any) -> None:
        pass

    async def check_is_contains_similar(self, cached_storage: CacheStorage, item: Any) -> bool:
        raise TypeError


class UnrealizedCacheInvalidationStrategy(CacheInvalidationStrategy):

    def process_update(self, **kwargs: Any) -> None:
        pass

    def process_retrieve(self, **kwargs: Any) -> None:
        pass


class APIResponsesCacheInvalidationStrategy(CacheInvalidationStrategy):
    _validator_criteria = ("params", "json", "data", "headers")

    def __init__(self, cache_time: Union[float, int] = INFINITE):
        self._uncached = ("https://api.qiwi.com/partner/bill", "/sinap/api/v2/terms/")
        self._cache_time = cache_time

    def process_update(self, **kwargs: Any) -> None:
        for key in kwargs.keys():
            if any(key.startswith(coincidence) for coincidence in self._uncached):
                raise ContainsNonCacheable()

    def process_retrieve(self, **kwargs: Any) -> None:
        self._have_cache_expired(**kwargs)

    def _have_cache_expired(self, **kwargs: Dict[str, Union[Any, float]]) -> None:
        for key, value in kwargs.items():
            added_at: float = value[ADD_TIME_PLACEHOLDER]
            elapsed_time_since_adding = time.monotonic() - added_at
            if elapsed_time_since_adding >= self._cache_time:
                raise CacheExpired()

    async def check_is_contains_similar(self, storage: CacheStorage, item: Any) -> bool:
        values = await storage.retrieve_all()
        if not isinstance(item, Payload):
            return item in values
        for value in values:
            if not isinstance(value, CachedAPIRequest):
                continue
            if (
                    value.method == "GET"
                    and value.payload.headers == item.headers  # noqa: W503
                    and value.payload.params == item.params  # noqa: W503
            ):
                return True
            else:
                if value.method == "GET":
                    return False
                keys = (k for k in self._validator_criteria if k != "headers")
                return any(getattr(item, key) == getattr(value.payload, key) for key in keys)
        return False


class CacheStorage(abc.ABC):

    def __init__(self, invalidate_strategy: Optional[CacheInvalidationStrategy] = None):
        if invalidate_strategy is None:
            invalidate_strategy = UnrealizedCacheInvalidationStrategy()
        self._invalidate_strategy: CacheInvalidationStrategy = invalidate_strategy

    @abc.abstractmethod
    def clear(self) -> None:
        pass

    @abc.abstractmethod
    def update(self, **kwargs: Any) -> None:
        pass

    @abc.abstractmethod
    async def retrieve(self, key: str) -> Any:
        pass

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        pass

    @abc.abstractmethod
    async def retrieve_all(self) -> List[Any]:
        ...

    def __getitem__(self, item: Any) -> Any:
        return self.retrieve(item)

    def __setitem__(self, key: str, value: Any) -> Any:
        self.update(**{key: value})


class InMemoryCacheStorage(CacheStorage):
    __slots__ = ("_data", "_invalidate_strategy")

    def __init__(self, invalidate_strategy: Optional[CacheInvalidationStrategy] = None):
        CacheStorage.__init__(self, invalidate_strategy)
        self._data: Dict[Any, Any] = {}
        self._lock = asyncio.Lock()

    def clear(self) -> None:
        self._invalidate_strategy.process_delete()
        self._data.clear()

    async def retrieve_all(self) -> List[Optional[Any]]:
        tasks: List[Task[Optional[Any]]] = [
            asyncio.create_task(self.retrieve(key))
            for key in self._data.keys()
        ]
        return await asyncio.gather(*tasks)  # type: ignore  # noqa

    def update(self, **kwargs: Any) -> None:
        try:
            self._invalidate_strategy.process_update(**kwargs)
        except ContainsNonCacheable:
            return None
        embedded_data: Dict[Any, Any] = _embed_cache_time(**kwargs)
        self._data.update(embedded_data)

    async def retrieve(self, key: str) -> Optional[Any]:
        async with self._lock:
            obj = self._data.get(key)
        if obj is None:
            return obj
        try:
            self._invalidate_strategy.process_retrieve(obj=obj)
            return obj[VALUE_PLACEHOLDER]
        except CacheExpired:
            self.delete(key)
            return None

    def delete(self, key: str) -> None:
        del self._data[key]

    async def contains_similar(self, item: Any) -> bool:
        return await self._invalidate_strategy.check_is_contains_similar(self, item)
