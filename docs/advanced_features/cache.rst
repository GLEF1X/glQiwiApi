=============
Query caching
=============

glQiwiApi provides builtin cache storage and cache invalidation strategies
such a `InMemoryCacheStorage` and `APIResponsesCacheInvalidationStrategy` accordingly.
Obviously, you can extend functionality of library and add, for example, Redis based cache storage.



.. tip:: By default InMemoryCacheStorage use `UnrealizedCacheInvalidationStrategy` as an invalidation strategy

Straightforward example
-----------------------

.. code-block:: python

    import asyncio

    from glQiwiApi.core.cache import InMemoryCacheStorage

    storage = InMemoryCacheStorage()  # here is UnrealizedCacheInvalidationStrategy as an invalidation strategy
    storage.update(cached=5)
    cached = storage.retrieve("cached")
    print(f"You have cached {cached}")

Advanced usage
--------------

This very cache invalidation by timer strategy is worth using if you want to achieve cache invalidation.
It should be noted that previous `UnrealizedCacheInvalidationStrategy` just ignores the invalidation and don't get rid of aged cache.

.. code-block:: python

    import time

    from glQiwiApi.core.cache import InMemoryCacheStorage, CacheInvalidationByTimerStrategy

    storage = InMemoryCacheStorage(CacheInvalidationByTimerStrategy(cache_time_in_seconds=1))

    storage.update(x=5)

    time.sleep(1)

    value = storage.retrieve("x")  # None
