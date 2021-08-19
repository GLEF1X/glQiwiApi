==============================
Class-based handlers & filters
==============================

.. tip:: **This section, like all the source library code, is supported by the mypy linter😁.**

Class-based filters
~~~~~~~~~~~~~~~~~~~

🧙Starting with 1.0.3b2 you can use class-based filters. Here is dive-in example of usage.

.. code-block:: python

    from glQiwiApi import QiwiWrapper, BaseFilter, types
    from glQiwiApi.utils import executor

    wrapper = QiwiWrapper(secret_p2p="secret key")


    class MyCustomFilter(BaseFilter):
        async def check(self, update: types.WebHook) -> bool:
            return update.version == "1.0.0"  # some expression or complicated interaction with update


    @wrapper.transaction_handler(MyCustomFilter())
    async def my_handler(update: types.WebHook):
        """some stuff with update"""


    executor.start_webhook(wrapper)


Class-based handlers
~~~~~~~~~~~~~~~~~~~~

Also, starting with 1.0.4 you can easily interact with class-based handlers.

Example of usage with decorator:

.. code-block:: python

    some_credentials = {
        "api_access_token": "some_token",
        "phone_number": "+some_number"
    }
    wrapper = QiwiWrapper(**some_credentials)

    @wrapper.transaction_handler()
    class MyTxnHandler(AbstractTransactionHandler):

        async def process_event(self) -> Any:
            print("HELLO FROM CLASS-BASED handler")