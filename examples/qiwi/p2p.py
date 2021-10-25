import asyncio

from glQiwiApi import QiwiWrapper


async def main():
    # You can pass on only p2p tokens, if you want to use only p2p api
    async with QiwiWrapper(
            secret_p2p="your_secret_p2p"
    ) as w:
        # This way you can create P2P bill using QIWI p2p API
        bill = await w.create_p2p_bill(
            amount=1,
            comment='my_comm'
        )
        # This way you can check status of transaction(exactly is transaction was paid)
        if (await w.check_p2p_bill_status(bill_id=bill.bill_id)) == 'PAID':
            print('You have successfully paid your invoice')
        else:
            print('Invoice was not paid')
        # Or, you can use method check on the instance of Bill
        print(await bill.check())


asyncio.run(main())
