import asyncio

from glQiwiApi import QiwiWrapper


async def p2p_test():
    wallet = QiwiWrapper(
        api_access_token='your_token',
        phone_number='+your_number',
        public_p2p='your_public_p2p_token',
        secret_p2p='your_secret_p2p_token'
    )
    # bill id будет сгенерирован как str(uuid.uuid4()), если не был передан
    bill = await wallet.create_p2p_bill(
        amount=1,
        comment='Im using glQiwiApi'
    )
    print(bill)
    # Так можно проверить статус на оплаченный
    status = (await wallet.check_p2p_bill_status(
        bill_id=bill.bill_id
    )) == 'PAID'
    print(status)
    bills = await wallet.p2p_orders()
    print(bills)


asyncio.run(p2p_test())
