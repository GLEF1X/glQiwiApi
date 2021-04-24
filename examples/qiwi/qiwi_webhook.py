import logging

from aiogram import Bot

from glQiwiApi import QiwiWrapper, types
from glQiwiApi.core.web_hooks.config import Path

TOKEN = 'token from https://qiwi.com/api/'
QIWI_SECRET = 'secret token from https://qiwi.com/p2p-admin/'

wallet = QiwiWrapper(
    api_access_token=TOKEN,
    secret_p2p=QIWI_SECRET
)

bot = Bot(token="BOT_TOKEN")


# There is a lambda expression for "cutting off" test payments
@wallet.transaction_handler(lambda event: event.payment is not None)
async def main(event: types.WebHook):
    logging.info("New transaction: %s", event)
    await bot.send_message(chat_id='1219185039', text=event.hook_id)


@wallet.bill_handler()
async def main2(event: types.Notification):
    logging.info("P2P EVENT %s", event)


# Custom format for logging
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Also, you can specify a path for webhook
# Example: http://127.0.0.1/your_path/
# If you don't pass path in `start_webhook`
# or dont pass on transaction_path or bill_path
# Its ok, because it will take a default paths
# default transaction_path = /web_hooks/qiwi/
# default bill_path = /webhooks/qiwi/bills/
# So, if you dont pass on paths
# you need to register webhook with url like
# on this example: http://your_ip:port/web_hooks/qiwi/ - for transactions
# or http://your_ip:port/webhooks/qiwi/bills/ - for bills
path = Path(
    transaction_path="/web_hooks/qiwi",
    bill_path="/my_webhook/"
)

wallet.start_webhook(
    # You can pass on any port, but it must be open for web
    # You can use any VPS server to catching webhook or
    # your configured local machine
    port=8080,
    level=logging.INFO,
    format=FORMAT,
    path=path
)
