import asyncio

from glQiwiApi import QiwiWrapper, RequestError

PUBLIC_KEY = 'P2P PUBLIC_KEY'
SECRET_KEY = 'P2P SECRET_KEY'


async def p2p_usage():
    async with QiwiWrapper(secret_p2p=SECRET_KEY, public_p2p=PUBLIC_KEY) as w:
        # bill id будет сгенерирован как str(uuid.uuid4()), если не был передан
        bill = await w.create_p2p_bill(
            amount=1,
            comment='Im using glQiwiApi'
        )
        print(bill)
        # Так можно проверить статус на оплаченный
        status = (await w.check_p2p_bill_status(
            bill_id=bill.bill_id
        )) == 'PAID'
        # Или, начиная с версии 0.2.0
        status = await bill.check()
        print(status)
        # Это выдаст ошибку, так как не передан api_access_token и phone_number
        # Вы можете в любой момент переназначить токен или номер
        try:
            await w.get_bills(rows=50)
        except RequestError as ex:
            print(ex)
        # Переназначаем токены
        w.api_access_token = 'TOKEN from https://qiwi.api'
        w.phone_number = '+NUMBER'
        print(await w.get_bills(rows=20))


asyncio.run(p2p_usage())
