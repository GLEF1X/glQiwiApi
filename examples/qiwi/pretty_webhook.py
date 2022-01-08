from glQiwiApi import QiwiWallet
from glQiwiApi.core.dispatcher.webhooks.config import (
    WebhookConfig,
    EncryptionConfig,
    ApplicationConfig,
)
from glQiwiApi.qiwi.types import TransactionWebhook, BillWebhook
from glQiwiApi.utils import executor

wallet = QiwiWallet(
    api_access_token="token from https://qiwi.com/api/",
)


@wallet.transaction_handler(lambda event: ...)
async def get_transaction(event: TransactionWebhook):
    print(event)


@wallet.bill_handler()
async def fetch_bill(notification: BillWebhook):
    print(notification)


executor.start_webhook(
    wallet,
    webhook_config=WebhookConfig(
        encryption=EncryptionConfig(secret_p2p_key="bla-bla-bla"),
        app=ApplicationConfig(port=80, host="your host"),
    ),
)
