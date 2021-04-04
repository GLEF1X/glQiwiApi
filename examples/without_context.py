# Здесь представлен пример без контекста async with
import asyncio

from glQiwiApi import QiwiWrapper

# Создаем объект кошелька и обязательно передаем without_context = True, иначе будут проблемы с aiohttp.ClientSession
wallet = QiwiWrapper(
    api_access_token='YOUR_TOKEN',
    phone_number="+YOUR_NUMBER",
    without_context=True
)


async def old_usage():
    print(await wallet.get_balance())


asyncio.run(old_usage())
