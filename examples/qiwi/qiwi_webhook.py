from aiogram import Bot

from glQiwiApi import QiwiWrapper, types
from glQiwiApi.core.dispatcher.webhooks.config import Path
from glQiwiApi.utils import executor

TOKEN = "token from https://qiwi.com/api/"
QIWI_SECRET = "secret token from https://qiwi.com/p2p-admin/"

wallet = QiwiWrapper(api_access_token=TOKEN, secret_p2p=QIWI_SECRET)

bot = Bot(token="BOT_TOKEN")


# There is a lambda expression for "cutting off" test payments
@wallet.transaction_handler(lambda event: event.payment is not None)
async def main(event: types.WebHook):
    event.client.dispatcher.logger.info("New transaction: {}", event)
    await bot.send_message(chat_id="1219185039", text=event.hook_id)


@wallet.bill_handler()
async def main2(event: types.Notification):
    event.client.dispatcher.logger.info("P2P EVENT {}", event)


# Also, you can specify a path for webhook
# Example: http://127.0.0.1/your_path/
# If you don't pass path in `start_webhook`
# or dont pass on transaction_path or bill_path
# Its ok, because it will take a default paths
# default transaction_path = /dispatcher/qiwi/
# default bill_path = /webhooks/qiwi/bills/
# So, if you dont pass on paths
# you need to register webhook with url like
# on this example: http://your_ip:port/web_hooks/qiwi/ - for transactions
# or http://your_ip:port/webhooks/qiwi/bills/ - for bills
path = Path(transaction_path="/dispatcher/qiwi", bill_path="/my_webhook/")

executor.start_webhook(
    wallet,
    # You can pass on any port, but it must be open for web
    # You can use any VPS server to catching webhook or
    # your configured local machine
    path=path,
)
