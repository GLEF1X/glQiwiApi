import logging
from dataclasses import dataclass

from aiogram import Bot, Dispatcher
from aiogram import types

from glQiwiApi import QiwiWrapper
from glQiwiApi.plugins.telegram.polling import TelegramPollingPlugin
from glQiwiApi.types import Transaction
from glQiwiApi.utils import executor

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """This config can be loaded from env, yaml or any other source"""
    qiwi_api_access_token: str
    qiwi_phone_number: str

    bot_token: str


async def aiogram_message_handler(msg: types.Message):
    await msg.answer(text="Привет😇")


async def qiwi_transaction_handler(update: Transaction):
    assert isinstance(update, Transaction)
    print(update)


def on_startup(wrapper: QiwiWrapper) -> None:
    logger.info("This message logged on startup")


def run_application() -> None:
    config = Config(
        qiwi_api_access_token="",
        qiwi_phone_number="+phone number",
        bot_token="token from BotFather"
    )
    bot = Bot(config.bot_token)
    dp = Dispatcher(bot)
    dp.register_message_handler(aiogram_message_handler)

    wallet = QiwiWrapper(api_access_token=config.qiwi_api_access_token, phone_number=config.qiwi_phone_number)
    wallet.register_transaction_handler(qiwi_transaction_handler)

    # set dispatcher to wallet instance for register aiogram handlers
    wallet["dispatcher"] = dp

    executor.start_polling(wallet, TelegramPollingPlugin(dp), on_startup=on_startup)


if __name__ == '__main__':
    run_application()
