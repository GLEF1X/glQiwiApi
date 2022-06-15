from __future__ import annotations

import abc
import time
from typing import TYPE_CHECKING, Any, Dict, Union

from glQiwiApi.core.cache.cached_types import CachedAPIRequest, Payload
from glQiwiApi.core.cache.constants import ADD_TIME_PLACEHOLDER
from glQiwiApi.core.cache.exceptions import CacheExpiredError, CacheValidationError

if TYPE_CHECKING:
    from glQiwiApi.core.cache.storage import CacheStorage

INFINITE = float('inf')


class CacheInvalidationStrategy(abc.ABC):
    @abc.abstractmethod
    async def process_update(self, **kwargs: Any) -> None:
        pass

    async def process_delete(self) -> None:
        pass

    @abc.abstractmethod
    async def process_retrieve(self, **kwargs: Any) -> None:
        pass

    async def check_is_contains_similar(self, cache_storage: CacheStorage, item: Any) -> bool:
        raise TypeError

    @property
    def is_cache_disabled(self) -> bool:
        return False


class UnrealizedCacheInvalidationStrategy(CacheInvalidationStrategy):
    async def process_update(self, **kwargs: Any) -> None:
        pass

    async def process_retrieve(self, **kwargs: Any) -> None:
        pass

    @property
    def is_cache_disabled(self) -> bool:
        return True


class CacheInvalidationByTimerStrategy(CacheInvalidationStrategy):
    def __init__(self, cache_time_in_seconds: Union[float, int] = INFINITE):
        self._cache_time = cache_time_in_seconds

    @property
    def is_cache_disabled(self) -> bool:
        return self._cache_time == 0

    async def process_update(self, **kwargs: Any) -> None:
        if self.is_cache_disabled:
            raise CacheValidationError()

    async def process_retrieve(self, **kwargs: Any) -> None:
        self._is_cache_expired(**kwargs)

    def _is_cache_expired(self, **kwargs: Dict[str, Union[Any, float]]) -> None:
        for key, value in kwargs.items():
            added_at: float = value[ADD_TIME_PLACEHOLDER]
            elapsed_time_since_adding = time.monotonic() - added_at
            if elapsed_time_since_adding >= self._cache_time:
                raise CacheExpiredError()


class APIResponsesCacheInvalidationStrategy(CacheInvalidationByTimerStrategy):
    _validation_criteria = ('params', 'json', 'data', 'headers')

    def __init__(self, cache_time_in_seconds: Union[float, int] = INFINITE):
        super().__init__(cache_time_in_seconds)
        self._uncached = ('https://api.qiwi.com/partner/bill', '/sinap/api/v2/terms/')

    @property
    def is_cache_disabled(self) -> bool:
        return self._cache_time == 0

    async def process_update(self, **kwargs: Any) -> None:
        await super().process_update(**kwargs)
        for key in kwargs.keys():
            if any(key.startswith(coincidence) for coincidence in self._uncached):
                raise CacheValidationError()

    async def check_is_contains_similar(self, storage: CacheStorage, item: Any) -> bool:
        values = await storage.retrieve_all()
        if not isinstance(item, Payload):
            return item in values
        for value in values:
            if not isinstance(value, CachedAPIRequest):
                continue
            if (
                value.method == 'GET'
                and value.payload.headers == item.headers  # noqa: W503
                and value.payload.params == item.params  # noqa: W503
            ):
                return True
            else:
                if value.method == 'GET':
                    return False
                keys = (k for k in self._validation_criteria if k != 'headers')
                return any(getattr(item, key) == getattr(value.payload, key) for key in keys)
        return False
