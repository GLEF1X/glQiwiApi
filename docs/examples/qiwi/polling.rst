================
Polling updates
================

.. tip:: 👩🏻🎨 ``start_polling`` has the same signature as ``start_webhook`` "under the hood"

Guidelines
~~~~~~~~~~

👩🏻🔬This API method gives a chance to hook updates without webhooks on your machine,
but it's possible to use both approaches anyway.


🧑🎓 *First of all, before starting polling, you need to register handlers, just like when installing webhooks.*
Lets do it with decorators, *but you also can do it another way, using* ``wallet.register_transaction_handler``,
``wallet.register_bill_handler`` or ``wallet.register_error_handler``

.. literalinclude:: ./../../../examples/qiwi/polling.py
    :caption: Add handlers
    :language: python
    :emphasize-lines: 12-14

🧙♀️So, we also have to import ``executor`` :ref:`Executor overview` and pass on our client,
that contains user-friendly functions ``start_polling`` and ``start_webhook``.

.. literalinclude:: ./../../../examples/qiwi/polling.py
    :caption: import executor module
    :language: python
    :emphasize-lines: 4, 24


Events
~~~~~~

👨🔬 Then, you can start polling, but, let's make it clear which arguments you should pass on to ``start_polling`` function.
You can also specify events like ``on_shutdown`` or ``on_startup``.

.. literalinclude:: ./../../../examples/qiwi/polling.py
    :language: python
    :emphasize-lines: 23

😼 As you can see, in the example we have a function that we pass as an argument to ``on_startup``.
As you may have guessed, this function will be executed at the beginning of the polling.

.. literalinclude:: ./../../../examples/qiwi/polling.py
    :language: python


Aiogram + glQiwiApi = friends🤩
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

🧚♀️ *Also, you can very easily implement simultaneous polling of updates from both aiogram and QIWI API.*

In the example below, we catch all text messages and return the same "Hello" response.

.. literalinclude:: ./../../../examples/qiwi/aiogram_integration.py
    :caption: polling together with aiogram
    :language: python

Error handling
~~~~~~~~~~~~~~

.. literalinclude:: ./../../../examples/qiwi/error_handling.py
    :language: python

Example usage without global variables😇
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ./../../../examples/qiwi/polling_without_global_variables.py
    :language: python
