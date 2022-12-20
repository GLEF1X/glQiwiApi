import asyncio

from glQiwiApi import QiwiWallet


async def main():
    async with QiwiWallet(api_access_token="",phone_number="+380985272064") as w:
        print(await w.get_balance())

asyncio.run(main())
