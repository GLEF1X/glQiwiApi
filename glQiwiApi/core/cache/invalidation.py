from __future__ import annotations

import abc
import time
from typing import TYPE_CHECKING, Any, Dict, Union

from glQiwiApi.core.cache.cached_types import CachedAPIRequest, Payload
from glQiwiApi.core.cache.constants import ADD_TIME_PLACEHOLDER
from glQiwiApi.core.cache.exceptions import CacheExpiredError, CacheValidationError

if TYPE_CHECKING:
    from glQiwiApi.core.cache.storage import CacheStorage

INFINITE = float("inf")


class CacheInvalidationStrategy(abc.ABC):
    @abc.abstractmethod
    def process_update(self, **kwargs: Any) -> None:
        pass

    def process_delete(self) -> None:
        pass

    @abc.abstractmethod
    def process_retrieve(self, **kwargs: Any) -> None:
        pass

    def check_is_contains_similar(self, cached_storage: CacheStorage, item: Any) -> bool:
        raise TypeError

    @property
    def is_cache_disabled(self) -> bool:
        return False


class UnrealizedCacheInvalidationStrategy(CacheInvalidationStrategy):
    def process_update(self, **kwargs: Any) -> None:
        pass

    def process_retrieve(self, **kwargs: Any) -> None:
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

    def process_update(self, **kwargs: Any) -> None:
        if self.is_cache_disabled:
            raise CacheValidationError()

    def process_retrieve(self, **kwargs: Any) -> None:
        self._have_cache_expired(**kwargs)

    def _have_cache_expired(self, **kwargs: Dict[str, Union[Any, float]]) -> None:
        for key, value in kwargs.items():
            added_at: float = value[ADD_TIME_PLACEHOLDER]
            elapsed_time_since_adding = time.monotonic() - added_at
            if elapsed_time_since_adding >= self._cache_time:
                raise CacheExpiredError()


class APIResponsesCacheInvalidationStrategy(CacheInvalidationByTimerStrategy):
    _validator_criteria = ("params", "json", "data", "headers")

    def __init__(self, cache_time_in_seconds: Union[float, int] = INFINITE):
        super().__init__(cache_time_in_seconds)
        self._uncached = ("https://api.qiwi.com/partner/bill", "/sinap/api/v2/terms/")

    @property
    def is_cache_disabled(self) -> bool:
        return self._cache_time == 0

    def process_update(self, **kwargs: Any) -> None:
        super().process_update(**kwargs)
        for key in kwargs.keys():
            if any(key.startswith(coincidence) for coincidence in self._uncached):
                raise CacheValidationError()

    def check_is_contains_similar(self, storage: CacheStorage, item: Any) -> bool:
        values = storage.retrieve_all()
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
