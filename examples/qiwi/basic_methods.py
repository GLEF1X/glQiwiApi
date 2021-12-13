import asyncio
import datetime

from glQiwiApi import QiwiWrapper, APIError
from glQiwiApi.types import TransactionType

TOKEN = "YOUR_API_ACCESS_TOKEN"
WALLET = "+NUMBER"
SECRET_KEY = "YOUR_SECRET_P2P_TOKEN"


async def basic_usage():
    async with QiwiWrapper(
        api_access_token=TOKEN, phone_number=WALLET, secret_p2p=SECRET_KEY
    ) as wallet:
        # So you can get information on a transaction, knowing its ID and type
        print(
            await wallet.transaction_info(
                transaction_type=TransactionType.OUT, transaction_id=21249852701
            )
        )
        # This way you can get the statistics of the qiwi wallet
        # difference between end_date and start_date must be less than 90 days
        stats = await wallet.fetch_statistics(
            start_date=datetime.datetime.now() - datetime.timedelta(days=10),
            end_date=datetime.datetime.now(),
        )
        print(stats)
        # Full account information
        info = await wallet.get_account_info()
        # Get the ip address from which the last login was made
        print(info.auth_info.ip)
        # We transfer money to another wallet, while receiving the ID of the payment
        payment_id = await wallet.transfer_money(
            amount=999, to_phone_number="some_number", comment="I love glQiwiApi"
        )
        print(payment_id)
        # handling types exceptions and get json representation
        try:
            await wallet.transfer_money(to_phone_number="+WRONG_NUMBER", amount=999)
        except APIError as ex:
            print(ex.json())


asyncio.run(basic_usage())
