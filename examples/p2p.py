import asyncio

from glQiwiApi import QiwiWrapper, RequestError

PUBLIC_KEY = '48e7qUxn9T7RyYE1MVZswX1FRSbE6iyCj2gCRwwF3Dnh5XrasNTx3BGPiMsyXQFNKQhvukniQG8RTVhYm3iPpzd6T6fUwiBX4WcjnHgoqxERdngWnH6EYfc7uBsGKPq4MF23dW4nUoixGqkoHj1YhjM7JyGfvh1o6fUdCHfX2uY8cfMxUFDwj8qRQgwPF'
SECRET_KEY = 'eyJ2ZXJzaW9uIjoiUDJQIiwiZGF0YSI6eyJwYXlpbl9tZXJjaGFudF9zaXRlX3VpZCI6ImJuMXZmNy0wMCIsInVzZXJfaWQiOiIzODA5NjgzMTc0NTkiLCJzZWNyZXQiOiI1MWY2MDc1MzkzYzgwZWZiY2FiM2Q5ZTVhNThjNjQ1NmE3ZWY4NjkxNDJkZjI0NjczNWYzNzZmZjkwODQwM2U4In19'


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
        w.api_access_token = '7f8e514786b0cd326cf604223ec91861'
        w.phone_number = '+380968317459'
        print(await w.get_bills(rows=20))


asyncio.run(p2p_usage())
