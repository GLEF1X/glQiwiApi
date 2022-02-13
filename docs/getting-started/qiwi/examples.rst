This section covers the most popular use cases of glQiwiApi.

How can I retrieve history?
--------------------------------


.. code-block:: python

    import asyncio

    from glQiwiApi import QiwiWallet


    async def get_history(qiwi_token: str, phone_number: str) -> None:
        async with QiwiWallet(api_access_token=qiwi_token, phone_number=phone_number) as wallet:
            for transaction in await wallet.history():
                # handle


    asyncio.run(get_history(qiwi_token="qiwi api token", phone_number="+phone number"))


How can I transfer money to other wallet?
-----------------------------------------

.. code-block:: python

    import asyncio

    from glQiwiApi import QiwiWallet


    async def transfer_money_to_another_wallet(qiwi_token: str, phone_number: str) -> None:
        async with QiwiWallet(api_access_token=qiwi_token, phone_number=phone_number) as wallet:
            await wallet.transfer_money(to_phone_number="+754545343", amount=1)


    asyncio.run(transfer_money_to_another_wallet(qiwi_token="token", phone_number="+phone number"))

How can I transfer money to other card?
---------------------------------------

.. code-block:: python

    import asyncio

    from glQiwiApi import QiwiWallet


    async def transfer_money_to_card(qiwi_token: str, phone_number: str) -> None:
        async with QiwiWallet(api_access_token=qiwi_token, phone_number=phone_number) as wallet:
            await wallet.transfer_money_to_card(card_number="desired card number", amount=50)


    asyncio.run(transfer_money_to_card(qiwi_token="token", phone_number="+phone number"))


How can I gracefully handle exceptions that may return API?
-----------------------------------------------------------

In most cases you just wrap the statement with method of API with `try/except` and then on demand get message(in json or plain text)
and log it

.. code-block:: python

    import asyncio

    from glQiwiApi import QiwiWallet
    from glQiwiApi.qiwi.exceptions import QiwiAPIError


    async def main():
        async with QiwiWallet(api_access_token="",
                              phone_number="+") as wallet:
            try:
                await wallet.transfer_money(to_phone_number="wrong number", amount=-1)
            except QiwiAPIError as ex:
                ex.json()  # json response from API
                print(ex)  # full traceback


    asyncio.run(main())

How to interact with P2P API?
-----------------------------

To create p2p bill you have to utilize `create_p2p_bill` method.

.. code-block:: python

    import asyncio

    from glQiwiApi import QiwiP2PClient


    async def create_p2p_bill():
        async with QiwiP2PClient(secret_p2p="your p2p token") as p2p:
            bill = await p2p.create_p2p_bill(amount=1)
            print(f"Link to pay bill with {bill.id} id = {bill.pay_url}")


    asyncio.run(create_p2p_bill())

If you go to the created link, you will see this:


.. image:: https://i.ibb.co/T0C5RYz/2021-03-21-14-58-33.png
   :width: 700
   :alt: bill form example

Obviously, you have to check this bill someway.
You can use handy label `p2p.check_if_bill_was_paid` or do it in standard way `p2p.get_bill_status(bill.bill_id)`
and then check that status equals appropriate value.

.. tip:: To reject p2p bill you should use `reject_p2p_bill` or label `p2p.reject()`

.. code-block:: python

    from glQiwiApi import QiwiP2PClient


    async def create_and_check_p2p_bill():
        async with QiwiP2PClient(secret_p2p="your p2p token") as p2p:
            bill = await p2p.create_p2p_bill(amount=777)
            if await p2p.check_if_bill_was_paid(bill):
                # some logic

Issue with referrer
-------------------

> QIWI block wallets users of which go to p2p pages from messengers, email and other services.

Currently, It's solved by reverse proxy, that deployed directly to AWS beanstalk.

`Bill.shim_url` property is a proxy url, that can be used to add `referrer` and try to avoid of blocking wallet.

.. code-block:: python

    import asyncio

    from glQiwiApi import QiwiP2PClient


    async def main():
        async with QiwiP2PClient(
                secret_p2p="Your secret p2p api key",
                shim_server_url="qiwi-proxy.us-east-2.elasticbeanstalk.com/proxy/p2p/{0}"
            ) as client:
            bill = await client.create_p2p_bill(amount=1)
            print(bill.shim_url)  # url to proxy


    asyncio.run(main())


But also you can transmit your own shim url directly to QiwiP2PClient constructor:

.. code-block:: python

    import asyncio

    from glQiwiApi import QiwiP2PClient


    async def main():
        async with QiwiP2PClient(
                secret_p2p="Your secret p2p api key",
                shim_server_url="https://some.url/proxy/p2p/{0}"
        ) as client:
            bill = await client.create_p2p_bill(amount=1)
            shim_url = client.create_shim_url(bill.invoice_uid)


    asyncio.run(main())

More methods you can figure out in  :doc:`autogenerated API docs <API/index>`

