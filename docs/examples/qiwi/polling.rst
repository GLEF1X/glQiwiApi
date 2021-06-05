================
Polling updates
================

.. tip:: 👩🏻🎨 ``start_polling`` has the same signature as ``start_webhook`` "under the hood"

👩🏻🔬This API method gives a chance to hook updates without webhooks on your machine,
but it's possible to use both approaches anyway.


🧑🎓 *First of all, before starting polling, you need to register handlers, just like when installing webhooks.*
Lets do it with decorators, *but we also can do it another way, using* ``wallet.dispatcher.register_transaction_handler``

.. literalinclude:: ./../../../examples/qiwi/polling.py
    :caption: Add handlers
    :language: python
    :emphasize-lines: 15-17

🧙♀️So, we also have to import ``executor`` :ref:`Executor overview` and pass on our client,
that contains user-friendly functions ``start_polling`` and ``start_webhook``.

.. literalinclude:: ./../../../examples/qiwi/polling.py
    :caption: import executor module
    :language: python
    :emphasize-lines: 4, 24

👨🔬 Then, you can start polling, but, let's make it clear which arguments you should pass on to ``start_polling`` function.
So, in this example we see ``get_updates_from`` and ``on_startup``, it means, that in example we want to receive notifications that came an hour
ago and execute some function on startup of polling updates


.. literalinclude:: ./../../../examples/qiwi/polling.py
    :caption: Args of polling
    :language: python
    :emphasize-lines: 26-27

😼 As you can see, in the example we have a function that we pass as an argument to ``on_startup``.
As you may have guessed, this function will be executed at the beginning of the polling.

.. literalinclude:: ./../../../examples/qiwi/polling.py
    :caption: Args of polling
    :language: python
    :emphasize-lines: 20-21,27

😻 If you did everything correctly, you will get something like this

.. code-block:: bash

    2021-06-05 17:21:07.423 | DEBUG    | glQiwiApi.utils.executor:welcome:373 - Start polling!

🧚♀️ *Also, you can very easily implement simultaneous polling of updates from both aiogram and QIWI API.*

In the example below, we catch all text messages and return the same "Hello" response.

.. literalinclude:: ./../../../examples/qiwi/aiogram_integration.py
    :caption: polling together with aiogram
    :language: python
    :emphasize-lines: 12-13,38,21-23,1-2,5,6
