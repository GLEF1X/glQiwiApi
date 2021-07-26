.. currentmodule:: glQiwiApi

=============
API reference
=============

Payment wrappers
----------------

.. automodule:: glQiwiApi
    :members: QiwiWrapper, YooMoneyAPI, QiwiMaps

Qiwi webhooks and polling API
-----------------------------

.. automodule:: glQiwiApi.core.web_hooks.filter
   :members:

.. automodule:: glQiwiApi.core.web_hooks.dispatcher
   :members:

.. automodule:: glQiwiApi.core.web_hooks.server
   :members:

.. _Executor overview:

.. automodule:: glQiwiApi.utils.executor
   :members:


Low level API
-------------

.. automodule:: glQiwiApi.core.basic_requests_api
   :members:

.. automodule:: glQiwiApi.core.aiohttp_custom_api
   :members:

.. automodule:: glQiwiApi.core.storage
   :members:


Aiogram integration
-------------------

.. automodule:: glQiwiApi.core.builtin.telegram
    :members:


Synchronous adapter
-------------------
.. automodule:: glQiwiApi.utils.api_helper
    :members: sync, await_sync, run_forever_safe, async_as_sync


Exceptions
----------
.. automodule:: glQiwiApi.utils.errors
   :members:


