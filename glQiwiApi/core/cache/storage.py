from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional

from glQiwiApi.core.cache.constants import VALUE_PLACEHOLDER
from glQiwiApi.core.cache.exceptions import CacheExpiredError, CacheValidationError
from glQiwiApi.core.cache.invalidation import (
    CacheInvalidationStrategy,
    UnrealizedCacheInvalidationStrategy,
)
from glQiwiApi.core.cache.utils import embed_cache_time


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
    def retrieve(self, key: str) -> Any:
        pass

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        pass

    @abc.abstractmethod
    def retrieve_all(self) -> List[Any]:
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

    def clear(self) -> None:
        self._invalidate_strategy.process_delete()
        self._data.clear()

    def retrieve_all(self) -> List[Optional[Any]]:
        return [self.retrieve(key) for key in list(self._data.keys())]

    def update(self, **kwargs: Any) -> None:
        try:
            self._invalidate_strategy.process_update(**kwargs)
        except CacheValidationError:
            return None
        embedded_data: Dict[Any, Any] = embed_cache_time(**kwargs)
        self._data.update(embedded_data)

    def retrieve(self, key: str) -> Optional[Any]:
        obj = self._data.get(key)
        if obj is None:
            return obj
        try:
            self._invalidate_strategy.process_retrieve(obj=obj)
            return obj[VALUE_PLACEHOLDER]
        except CacheExpiredError:
            self.delete(key)
            return None

    def delete(self, key: str) -> None:
        del self._data[key]

    def contains_similar(self, item: Any) -> bool:
        return self._invalidate_strategy.check_is_contains_similar(self, item)

    def __del__(self) -> None:
        del self._data
