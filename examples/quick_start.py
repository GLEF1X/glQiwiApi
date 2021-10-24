import asyncio

from glQiwiApi import QiwiWrapper, APIError


async def print_balance(qiwi_token: str, phone_number: str) -> None:
    """
    This function allows you to get balance of your wallet using glQiwiApi library
    """
    async with QiwiWrapper(api_access_token=qiwi_token, phone_number=phone_number) as w:
        try:
            balance = await w.get_balance()
        # handle exception if wrong credentials or really API return error
        except APIError as err:
            print(err.json())
            raise
    print(f"Your current balance is {balance.amount} {balance.currency.name}")


asyncio.run(print_balance(qiwi_token="qiwi api token", phone_number="+phone_number"))
