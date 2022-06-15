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

========
Examples
========

Dive-in example.

.. code-block:: python

    import asyncio

    from glQiwiApi import YooMoneyAPI

    TOKEN = 'your token'


    async def main():
        async with YooMoneyAPI(api_access_token=TOKEN) as w:
            print(await w.operation_history(records=50))


    asyncio.run(main())

Creating pay form.

.. tip:: This method is extremely weightless, cause it doesn't send any request.

.. code-block:: python

    from glQiwiApi import YooMoneyAPI

    TOKEN = 'your token'

    link = YooMoneyAPI.create_pay_form(
        receiver="4100116602400968",
        quick_pay_form="donate",
        targets="donation",
        payment_type="PC",
        amount=50
    )

    print(link)


Send money to another wallet and checking this transaction

.. code-block:: python

    import asyncio

    from glQiwiApi import YooMoneyAPI

    TOKEN = 'your_token'


    async def main():
        w = YooMoneyAPI(TOKEN)
        async with w:
            # So you can send funds to another account, in the example this is a transfer to account 4100116602400968
            # worth 2 rubles with the comment "I LOVE glQiwiApi"
            payment = await w.transfer_money(
                to_account='4100116602400968',
                comment='I LOVE glQiwiApi',
                amount=2
            )
            # This way you can check the transaction, whether it was received by the person on the account
            print(await w.check_if_operation_exists(
                check_fn=lambda o: o.id == payment.payment_id
            ))


    asyncio.run(main())


Fetch account info.

.. code-block:: python

    import asyncio

    from glQiwiApi import YooMoneyAPI

    TOKEN = 'your_token'


    async def main():
        w = YooMoneyAPI(TOKEN)
        async with w:
            # This gives you account information as AccountInfo pydantic model.
            get_account_info = await w.retrieve_account_info()
            print(get_account_info.account_status)
            print(get_account_info.balance)


    asyncio.run(main())
