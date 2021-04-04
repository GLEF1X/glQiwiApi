# Здесь представлен пример без контекста async with
import asyncio

from glQiwiApi import QiwiWrapper

# Создаем объект кошелька и обязательно передаем without_context = True, иначе будут проблемы с aiohttp.ClientSession
wallet = QiwiWrapper(
    api_access_token='7f8e514786b0cd326cf604223ec91861',
    phone_number="+380968317459",
    without_context=True
)


async def main():
    async with QiwiWrapper(secret_p2p='my_p2p') as w:
        w.public_p2p = 'my_public_p2p'
        bill = await w.create_p2p_bill(amount=1)
        # new version
        new_status = await bill.check()
        # old version
        old_status = (await w.check_p2p_bill_status(bill.bill_id)) == 'PAID'


asyncio.run(main())
