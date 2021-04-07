import asyncio

from glQiwiApi import QiwiWrapper


async def main():
    # If you want to use types wrapper without async context just
    # pass on "without_context=True"
    wallet = QiwiWrapper(
        api_access_token='your_token',
        phone_number='+number',
        without_context=True
    )
    print((await wallet.get_balance()).amount)


async def main_boost():
    # OR(x3 performance boost with async context,
    # because it use only 1 aiohttp session to get response for all requests
    # in async with context manager)
    async with QiwiWrapper(api_access_token='your_token') as w:
        w.phone_number = '+number'
        # Данным вызовом вы получите текущий баланс кошелька.
        print((await w.get_balance()).amount)


asyncio.run(main_boost())
