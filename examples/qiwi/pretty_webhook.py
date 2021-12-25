from glQiwiApi import QiwiWrapper, base_types
from glQiwiApi.utils import executor

wallet = QiwiWrapper(
    api_access_token="token from https://qiwi.com/api/",
    secret_p2p="secret token from https://qiwi.com/p2p-admin/",
)


@wallet.transaction_handler(lambda event: ...)
async def get_transaction(event: base_types.TransactionWebhook):
    print(event)


@wallet.bill_handler()
async def fetch_bill(notification: base_types.BillWebhook):
    print(notification)


executor.start_webhook(wallet, port=80)
