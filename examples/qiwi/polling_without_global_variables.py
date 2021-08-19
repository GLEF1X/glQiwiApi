from typing import cast

from aiogram import Bot, Dispatcher
from aiogram import types

from glQiwiApi import QiwiWrapper
from glQiwiApi.builtin import TelegramPollingProxy
from glQiwiApi.types import Transaction
from glQiwiApi.utils import executor

api_access_token = "your token"
phone_number = "+your number"


def run_application() -> None:
    bot = Bot("token from BotFather")
    dp = Dispatcher(bot)
    wallet = QiwiWrapper(api_access_token=api_access_token, phone_number=phone_number)

    # set dispatcher to wallet instance for register aiogram handlers
    wallet["dispatcher"] = dp

    executor.start_polling(wallet, on_startup=on_startup, tg_app=TelegramPollingProxy(dp), skip_updates=True)


def register_handlers(wrapper: QiwiWrapper):
    wrapper.register_transaction_handler(qiwi_transaction_handler)
    dispatcher = cast(Dispatcher, wrapper["dispatcher"])
    dispatcher.register_message_handler(aiogram_message_handler)


async def aiogram_message_handler(msg: types.Message):
    await msg.answer(text="Привет😇")


async def qiwi_transaction_handler(update: Transaction):
    assert isinstance(update, Transaction)
    print(update)


def on_startup(wrapper: QiwiWrapper) -> None:
    wrapper.dispatcher.logger.info("This message logged on startup")
    register_handlers(wrapper)


if __name__ == '__main__':
    run_application()
