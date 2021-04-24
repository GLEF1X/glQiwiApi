import logging

from aiogram import Bot

from glQiwiApi import QiwiWrapper, types

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
    logging.info(f"New transaction: {event}")
    await bot.send_message(chat_id='1219185039', text=event.hook_id)


@wallet.bill_handler()
async def main2(event: types.Notification):
    logging.info(f"P2P EVENT {event}")


# Custom format for logging
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

wallet.start_webhook(
    # You can pass on any port, but it must be open for web
    # You can use any VPS server to catching webhook or
    # your configured local machine
    port=8080,
    level=logging.INFO,
    format=FORMAT
)
