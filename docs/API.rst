.. currentmodule:: glQiwiApi

=============
API reference
=============

.. topic:: API reference

    Here you can find all API reference to glQiwiApi or almost all =)

Payment wrappers
----------------

Qiwi API
~~~~~~~~

.. automodule:: glQiwiApi
    :members: QiwiWrapper

YooMoney API
~~~~~~~~~~~~

.. automodule:: glQiwiApi
   :members: YooMoneyAPI

Qiwi maps API
~~~~~~~~~~~~~

.. automodule:: glQiwiApi
   :members: QiwiMaps

Qiwi webhooks and polling API
-----------------------------


.. automodule:: glQiwiApi.core.dispatcher
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

.. automodule:: glQiwiApi.core.abstracts
   :members:

Extensions
----------

.. automodule:: glQiwiApi.ext.ssl_configurator
   :members:

.. automodule:: glQiwiApi.ext.url_builder
   :members:

Aiogram integration
-------------------

.. automodule:: glQiwiApi.builtin.telegram
    :members:


Synchronous adapter
-------------------

.. automodule:: glQiwiApi.core.synchronous.decorator
    :members: sync, await_sync, run_forever_safe, async_as_sync

.. automodule:: glQiwiApi.core.synchronous.adapter
    :members:

.. automodule:: glQiwiApi.core.synchronous.model_adapter
   :members:


Exceptions
----------
.. automodule:: glQiwiApi.utils.errors
   :members:


