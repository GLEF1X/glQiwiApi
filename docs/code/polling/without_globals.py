import logging
from typing import cast

from aiogram import Bot, Dispatcher, types

from glQiwiApi import QiwiWrapper
from glQiwiApi.core.event_fetching import executor
from glQiwiApi.core.event_fetching.dispatcher import QiwiDispatcher
from glQiwiApi.core.event_fetching.executor import Context
from glQiwiApi.plugins import AiogramPollingPlugin
from glQiwiApi.qiwi.clients.wallet.types import Transaction

api_access_token = "token"
phone_number = "+phone number"

logger = logging.getLogger(__name__)


async def aiogram_message_handler(msg: types.Message):
    await msg.answer(text="Привет😇")


async def qiwi_transaction_handler(update: Transaction, ctx: Context):
    print(update)


def on_startup(ctx: Context) -> None:
    logger.info("This message logged on startup")
    register_handlers(ctx)


def register_handlers(ctx: Context):
    ctx["qiwi_dp"].transaction_handler()(qiwi_transaction_handler)
    dispatcher = cast(Dispatcher, ctx["dp"])
    dispatcher.register_message_handler(aiogram_message_handler)


def run_application() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot("BOT TOKEN")
    dp = Dispatcher(bot)
    wallet = QiwiWrapper(api_access_token=api_access_token, phone_number=phone_number)
    qiwi_dp = QiwiDispatcher()

    executor.start_polling(
        wallet,
        qiwi_dp,
        AiogramPollingPlugin(dp),
        on_startup=on_startup,
        skip_updates=True,
        context={"dp": dp, "qiwi_dp": qiwi_dp},
    )


if __name__ == "__main__":
    run_application()
