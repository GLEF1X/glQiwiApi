===========================
How to obtain the API token
===========================

Firstly, you have to register our application in YooMoney using the link: `click <https://yoomoney.ru/myservices/new>`_.

So, you will be redirected to the same page:

.. image:: https://i.imgur.com/Mu6R8Po.png
   :width: 700
   :alt: example of registration form

It goes without saying, we get the client_id after registration and then use `YooMoneyAPI`.
Here is brief example how to obtain url to get special `code`

.. code-block:: python

   import asyncio

   from glQiwiApi import YooMoneyAPI


   async def get_url_to_auth() -> None:
       # Get a link for authorization, follow it if we get invalid_request or some kind of error
       # means either the scope parameter is incorrectly passed, you need to reduce the list of rights or try to recreate the application
       print(await YooMoneyAPI.build_url_for_auth(
           # For payments, account verification and payment history, you need to specify scope = ["account-info", "operation-history", "operation-details", "payment-p2p"]
           scope=["account-info", "operation-history"],
           client_id='ID received when registering the application above',
           redirect_uri='the link specified during registration above in the Redirect URI field'
       ))


   asyncio.run(get_url_to_auth())


.. tip:: In the url you will see your code as a default param of GET request e.g. https://example.com/?code=bla-bla-bla



Now you need to get the temporary code and get the token as fast as possible using the YooMoneyAPI class method:

.. code-block:: python

    import asyncio

    from glQiwiApi import YooMoneyAPI


    async def get_token() -> None:
        print(await YooMoneyAPI.get_access_token(
            code='the code obtained from the link',
            client_id='Application ID received when registering the application above',
            redirect_uri='link provided during registration'
        ))


    asyncio.run(get_token())
