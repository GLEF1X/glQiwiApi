================
Polling updates
================

API internals
~~~~~~~~~~~~~

.. automodule:: glQiwiApi.core.event_fetching.executor
    :members: start_polling,start_non_blocking_qiwi_api_polling,configure_app_for_qiwi_webhooks
    :show-inheritance:
    :member-order: bysource
    :undoc-members: True

.. autoclass:: glQiwiApi.core.event_fetching.executor.BaseExecutor
    :members:
    :show-inheritance:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True

.. autoclass:: glQiwiApi.core.event_fetching.executor.PollingExecutor
    :members:
    :show-inheritance:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True

Guidelines
~~~~~~~~~~

This section explains how to properly poll transactions from QIWI API.


*You can't help registering handlers and start polling, so in example above it is shown how to do it rightly.*
Lets do it with decorators:

.. literalinclude:: code/qiwi/polling.py
    :language: python
    :emphasize-lines: 15,21

️So, we also have to import ``executor`` and pass on our client,
that contains functions ``start_polling`` and ``start_webhook``.

.. literalinclude:: code/polling/qiwi.py
    :language: python
    :emphasize-lines: 2


Events
~~~~~~

Then, you can start polling, but, let's make it clear which arguments you should pass on to ``start_polling`` function.
You can also specify events like ``on_shutdown`` or ``on_startup``.
As you can see, in the example we have a function that we pass as an argument to ``on_startup``.
As you may have guessed, this function will be executed at the beginning of the polling.

.. literalinclude:: code/polling/events.py
    :language: python
    :emphasize-lines: 17,21,26


Make aiogram work with glQiwiApi
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Also, you can very easily implement simultaneous polling of updates from both aiogram and QIWI API.*

In the example below, we catch all text messages and return the same "Hello" response.

.. literalinclude:: code/polling/with_aiogram.py
    :language: python

Alternatively you can run polling at ``on_startup`` event

.. literalinclude:: code/polling/with_aiogram_non_blocking.py
    :language: python

Example usage without global variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: code/polling/without_globals.py
    :language: python
