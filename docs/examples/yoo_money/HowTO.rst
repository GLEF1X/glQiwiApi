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
            print(await w.transactions(records=50))


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
        payment = await w.send(
          to_account='4100116602400968',
          comment='I LOVE glQiwiApi',
          amount=2
        )
        # This way you can check the transaction, whether it was received by the person on the account
        print(await w.check_transaction(amount=2, comment='I LOVE glQiwiApi',
                                        operation_type='out'))


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