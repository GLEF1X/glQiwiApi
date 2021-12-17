from __future__ import annotations

import time

import pytest

from glQiwiApi.core.cache import APIResponsesCacheInvalidationStrategy, InMemoryCacheStorage

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="permanent_storage")
def storage_with_infinite_cache_time() -> InMemoryCacheStorage:
    storage = InMemoryCacheStorage(APIResponsesCacheInvalidationStrategy())
    yield storage
    storage.clear()


@pytest.fixture()
def cache_time() -> float:
    return 0.1


@pytest.fixture(name="temporary_storage")
def storage_with_limited_cache_time(cache_time: float) -> InMemoryCacheStorage:
    storage = InMemoryCacheStorage(
        APIResponsesCacheInvalidationStrategy(cache_time_in_seconds=cache_time)
    )
    yield storage
    storage.clear()


def test_update(permanent_storage: InMemoryCacheStorage):
    permanent_storage.update(hello="world")
    assert permanent_storage.retrieve("hello") == "world"


def test_retrieve(permanent_storage: InMemoryCacheStorage):
    data = {"x": 5}
    permanent_storage.update(**data)
    assert permanent_storage.retrieve(list(data.keys())[0]) == list(data.values())[0]


def test_retrieve_all(permanent_storage: InMemoryCacheStorage):
    permanent_storage.update(x=5, y=7)
    assert permanent_storage.retrieve_all() == [5, 7]


def test_invalidation_by_cache_time(temporary_storage: InMemoryCacheStorage, cache_time: float):
    temporary_storage.update(x=5)
    time.sleep(cache_time + 0.01)
    assert temporary_storage.retrieve("x") is None


def test_clear(permanent_storage: InMemoryCacheStorage):
    permanent_storage.update(x=5, y=7)
    assert len(permanent_storage.retrieve_all()) != 0
    permanent_storage.clear()
    assert len(permanent_storage.retrieve_all()) == 0


def test_delete(permanent_storage: InMemoryCacheStorage):
    permanent_storage.update(x=2, y=3)
    permanent_storage.delete("x")
    assert permanent_storage.retrieve_all() == [3]
