import asyncio

from glQiwiApi import QiwiP2PClient

wallet = QiwiP2PClient(secret_p2p="your secret p2p")


async def main():
    bill = await wallet.create_p2p_bill(amount=1)
    # new versions
    new_status = await bill.check()  # or bill.paid
    # old version(0.x)
    old_status = (await wallet.get_bill_status(bill.id)) == "PAID"
    assert new_status == old_status
    await wallet.close()


asyncio.run(main())
