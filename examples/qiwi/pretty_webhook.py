import logging

from glQiwiApi import QiwiWrapper, types

wallet = QiwiWrapper(
    api_access_token='token from https://qiwi.com/api/',
    secret_p2p='secret token from https://qiwi.com/p2p-admin/'
)


@wallet.transaction_handler(lambda event: ...)
async def get_transaction(event: types.WebHook):
    print(event)


@wallet.bill_handler()
async def fetch_bill(notification: types.Notification):
    print(notification)


FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

wallet.start_webhook(
    port=80,
    level=logging.INFO,
    format=FORMAT
)
