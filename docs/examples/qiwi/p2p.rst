============
QIWI P2P API
============

To create p2p bill you have to utilize `create_p2p_bill` method. Let's go to superb example:

.. code-block:: python

   import asyncio

   from glQiwiApi import QiwiWrapper


   async def create_p2p_bill():
       async with QiwiWrapper(secret_p2p="your p2p token") as w:
           bill = await w.create_p2p_bill(amount=1)
       # probably, you wanna get pay url, so you can do it comfortably
       print(f"Link to pay bill with {bill.bill_id} id = {bill.pay_url}")


   asyncio.run(create_p2p_bill())

If you go to the created link, you will see this:

.. image:: https://i.ibb.co/T0C5RYz/2021-03-21-14-58-33.png
   :width: 700
   :alt: bill form example

Obviously, you have to check this bill someway. There are two ways to do it. Let's go to rapid example:

.. tip:: To reject p2p bill you should use `reject_p2p_bill` or `bill.reject()`

.. code-block:: python

   import asyncio

   from glQiwiApi import QiwiWrapper


   async def how_to_check_bill():
       # as shown above, we just create a bill
       async with QiwiWrapper(secret_p2p="your p2p token") as w:
           bill = await w.create_p2p_bill(amount=777)
       # laconic variant to check bill, but you might encounter to some problems with pickling it
       await bill.check()
       # So, you can use default API method
       status = await w.check_p2p_bill_status(bill.bill_id)
       if status == "PAID":
           print("It's ok")
       else:
           print("Bill was not paid")


   asyncio.run(how_to_check_bill())

