import asyncio

from glQiwiApi import QiwiWrapper

wallet = QiwiWrapper(
    api_access_token="token", phone_number="+number", secret_p2p="your secret p2p"
)


async def main():
    bill = await wallet.create_p2p_bill(amount=1)
    # new versions
    new_status = await bill.check()  # or bill.paid
    # old version(0.x)
    old_status = (await wallet.check_p2p_bill_status(bill.bill_id)) == "PAID"
    assert new_status == old_status
    await wallet.close()


asyncio.run(main())
