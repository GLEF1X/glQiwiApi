================
Polling updates
================

API internals
~~~~~~~~~~~~~

.. automodule:: glQiwiApi.utils.executor
    :members: start_polling
    :show-inheritance:
    :member-order: bysource
    :undoc-members: True

.. autoclass:: glQiwiApi.utils.executor.BaseExecutor
    :members:
    :show-inheritance:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True

.. autoclass:: glQiwiApi.utils.executor.PollingExecutor
    :members:
    :show-inheritance:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True

Guidelines
~~~~~~~~~~

This section explains how to properly poll transactions from QIWI API.


*You can't help registering handlers and start polling, so in example above it is shown how to do it rightly.*
Lets do it with decorators, but you can also do it another, more explicit way, using ``wallet.register_transaction_handler``,
``wallet.register_bill_handler`` or ``wallet.register_error_handler``

.. literalinclude:: ./../examples/qiwi/polling.py
    :language: python
    :emphasize-lines: 14-16

️So, we also have to import ``executor`` and pass on our client,
that contains user-friendly functions ``start_polling`` and ``start_webhook``.

.. literalinclude:: ./../examples/qiwi/polling.py
    :language: python


Events
~~~~~~

Then, you can start polling, but, let's make it clear which arguments you should pass on to ``start_polling`` function.
You can also specify events like ``on_shutdown`` or ``on_startup``.

.. literalinclude:: ./../examples/qiwi/polling.py
    :language: python
    :emphasize-lines: 23

As you can see, in the example we have a function that we pass as an argument to ``on_startup``.
As you may have guessed, this function will be executed at the beginning of the polling.

.. literalinclude:: ./../examples/qiwi/polling.py
    :language: python


Make aiogram work with glQiwiApi
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Also, you can very easily implement simultaneous polling of updates from both aiogram and QIWI API.*

In the example below, we catch all text messages and return the same "Hello" response.

.. literalinclude:: ./../examples/qiwi/aiogram_integration.py
    :language: python

Error handling
~~~~~~~~~~~~~~

.. literalinclude:: ./../examples/qiwi/error_handling.py
    :language: python

Example usage without global variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ./../examples/qiwi/polling_without_global_variables.py
    :language: python
