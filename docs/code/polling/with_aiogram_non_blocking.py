from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.utils import executor

from glQiwiApi import QiwiWallet
from glQiwiApi.core.event_fetching.dispatcher import QiwiDispatcher
from glQiwiApi.core.event_fetching.executor import Context, start_non_blocking_qiwi_api_polling
from glQiwiApi.qiwi.clients.wallet.types import Transaction

qiwi_dp = QiwiDispatcher()
wallet = QiwiWallet(api_access_token="token", phone_number="+phone number")

dp = Dispatcher(Bot("BOT TOKEN"))


@qiwi_dp.transaction_handler()
async def handle_transaction(t: Transaction, ctx: Context):
    """Handle transaction here"""


@dp.message_handler()
async def handle_message(msg: Message):
    await msg.answer(text="Hello world")


async def on_startup(dp: Dispatcher):
    await start_non_blocking_qiwi_api_polling(wallet, qiwi_dp)


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)
