import logging

from aiogram import Bot

from glQiwiApi import QiwiWallet
from glQiwiApi.core.dispatcher.webhooks.config import (
    WebhookConfig,
    EncryptionConfig,
    ApplicationConfig,
    RoutesConfig,
)
from glQiwiApi.qiwi.types import BillWebhook, TransactionWebhook
from glQiwiApi.utils import executor

TOKEN = "token from https://qiwi.com/api/"
QIWI_SECRET = "secret token from https://qiwi.com/p2p-admin/"

wallet = QiwiWallet(api_access_token=TOKEN)

bot = Bot(token="BOT_TOKEN")

logger = logging.getLogger(__name__)


# There is a lambda expression for "cutting off" test payments
@wallet.transaction_handler(lambda event: event.payment is not None)
async def main(event: TransactionWebhook):
    logger.info("New transaction: {}", event)
    await bot.send_message(chat_id="1219185039", text=event.id)


@wallet.bill_handler()
async def main2(event: BillWebhook):
    logger.info("P2P EVENT {}", event)


executor.start_webhook(
    wallet,
    webhook_config=WebhookConfig(
        encryption=EncryptionConfig(secret_p2p_key=QIWI_SECRET),
        app=ApplicationConfig(port=80, host="your host"),
        routes=RoutesConfig(p2p_path="/qiwi/api/p2p", standard_qiwi_hook_path="/qiwi/api/default"),
    ),
)
