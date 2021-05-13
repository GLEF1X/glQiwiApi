================
Polling updates
================

.. tip:: 👩🏻‍🎨 ``start_polling`` has the same signature as ``start_webhook``

👩🏻‍🔬This API method gives a chance to hook updates without webhooks on your machine,
but it's possible to use both approaches anyway.


🧑‍🎓 *First of all, before starting polling, you need to register handlers, just like when installing webhooks*

.. literalinclude:: ./../../../examples/qiwi/polling.py
    :caption: Add handlers
    :language: python
    :emphasize-lines: 14-16

👨‍🔬 Then, you can start polling, but, let's make it clear which arguments you should pass on to ``start_polling`` method.
So, in this example we see ``get_updates_from`` and ``on_startup``, it means, that in example we want to receive notifications that came an hour
ago and execute some function on startup of polling updates


.. literalinclude:: ./../../../examples/qiwi/polling.py
    :caption: Args of polling
    :language: python
    :emphasize-lines: 23-26

😼 As you can see, in the example we have a function that we pass as an argument to ``on_startup``.

As you may have guessed, this function will be executed at the beginning of the polling.

.. literalinclude:: ./../../../examples/qiwi/polling.py
    :caption: Args of polling
    :language: python
    :emphasize-lines: 19-20,25

😻 If you did everything correctly, you will get something like this

.. code-block:: bash

    2021-05-13 16:27:22,921 - [INFO] - Start polling!
    2021-05-13 16:27:22,922 - [INFO] - This message came on startup
    2021-05-13 16:27:23,938 - [INFO] - Stop polling!
