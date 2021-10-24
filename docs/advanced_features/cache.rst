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

    from glQiwiApi.core.storage import InMemoryCacheStorage, UnrealizedCacheInvalidationStrategy

    storage = InMemoryCacheStorage()  # here is UnrealizedCacheInvalidationStrategy as an invalidation strategy


    async def main():
        storage.update(cached=5)
        cached = await storage.retrieve("cached")
        print(f"You have cached {cached}")


    asyncio.run(main())
