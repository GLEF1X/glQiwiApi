from aiogram import Bot, Dispatcher
from aiogram import types

from glQiwiApi import QiwiWrapper
from glQiwiApi.builtin import TelegramPollingProxy
from glQiwiApi.types import Transaction
from glQiwiApi.utils import executor

api_access_token = "your token"
phone_number = "your number"

bot = Bot("token from BotFather")
dp = Dispatcher(bot)

wallet = QiwiWrapper(api_access_token=api_access_token, phone_number=phone_number)


@dp.message_handler()
async def message_handler(msg: types.Message):
    await msg.answer(text="Привет😇")


@wallet.transaction_handler()
async def my_first_handler(update: Transaction):
    assert isinstance(update, Transaction)


def on_startup(wrapper: QiwiWrapper):
    wrapper.dispatcher.logger.info("This message logged on startup")


executor.start_polling(wallet, on_startup=on_startup, tg_app=TelegramPollingProxy(dp))
