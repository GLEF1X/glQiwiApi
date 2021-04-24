=================
Synchronous usage
=================

*glQiwiApi* also coverage synchronous usage, you can use it like in the example.

.. tip:: Usage. **You can use this sync adapter for any async function**.

.. literalinclude:: ./../../../examples/other/sync_usage.py
    :caption: sync_usage.py
    :language: python
    :linenos:

Example of usage *sync* adapter for custom async function: ::

    import asyncio

    from glQiwiApi import sync


    async def some_async():
        await asyncio.sleep(2)


    def main():
        sync(some_async)


    main()
