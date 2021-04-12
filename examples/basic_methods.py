import asyncio
import datetime

from glQiwiApi import QiwiWrapper, RequestError

TOKEN = "YOUR_API_ACCESS_TOKEN"
WALLET = "+NUMBER"
PUBLIC_KEY = 'YOUR_PUBLIC_P2P_TOKEN'
SECRET_KEY = 'YOUR_SECRET_P2P_TOKEN'


async def basic_usage():
    async with QiwiWrapper(
            api_access_token=TOKEN,
            phone_number=WALLET,
            public_p2p=PUBLIC_KEY,
            secret_p2p=SECRET_KEY
    ) as wallet:
        # Так вы можете получить информацию по транзакции, зная её айди и тип
        print(await wallet.transaction_info(
            transaction_type='OUT', transaction_id=21249852701
        ))
        # Таким образом вы можете получить статистику киви кошелька
        # РАЗНИЦА МЕЖДУ end_date и start_date ДОЛЖНА БЫТЬ МЕНЬШЕ 90 ДНЕЙ
        stats = await wallet.fetch_statistics(
            start_date=datetime.datetime.now() - datetime.timedelta(days=10),
            end_date=datetime.datetime.now()
        )
        print(stats.out[0].amount)
        # Полная информация об аккаунте
        info = await wallet.account_info()
        # Получаем айпи адресс, с которого был совершен последний вход
        print(info.auth_info.ip)
        # Переводим деньги на другой кошелек, при этом получая айди платежа
        payment_id = await wallet.to_wallet(
            trans_sum=999,
            to_number="some_number",
            comment="I love glQiwiApi"
        )
        print(payment_id)
        # handling types exceptions and get json representation
        try:
            await wallet.to_wallet(to_number="+WRONG_NUMBER", trans_sum=999)
        except RequestError as ex:
            print(ex.json())


asyncio.run(basic_usage())
