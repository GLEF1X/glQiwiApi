import asyncio
import datetime

from glQiwiApi import YooMoneyAPI

TOKEN = "token"

wallet = YooMoneyAPI(api_access_token=TOKEN)


async def main():
    async with wallet as w:
        # Get operation_history
        print(
            await w.operation_history(
                operation_types=["DEPOSITION", "PAYMENT"],
                start_date=datetime.datetime.now() - datetime.timedelta(days=10),
                end_date=datetime.datetime.now(),
            )
        )
        # Get account info about account
        print(await w.retrieve_account_info())
        # Getting balance
        print(await w.get_balance())

        payment = await w.send(to_account="Some_account", amount=2, comment="i love glQiwiApi")
        print(payment)
        # Revoke the API token
        await w.revoke_api_token()


asyncio.run(main())
