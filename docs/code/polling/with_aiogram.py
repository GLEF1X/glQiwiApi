from aiogram import Bot, Dispatcher
from aiogram.types import Message

from glQiwiApi import QiwiWallet
from glQiwiApi.core.event_fetching import executor
from glQiwiApi.core.event_fetching.dispatcher import QiwiDispatcher
from glQiwiApi.core.event_fetching.executor import Context
from glQiwiApi.plugins import AiogramPollingPlugin
from glQiwiApi.qiwi.clients.wallet.types import Transaction

qiwi_dp = QiwiDispatcher()
wallet = QiwiWallet(api_access_token='token', phone_number='+phone number')

dp = Dispatcher(Bot('BOT TOKEN'))


@qiwi_dp.transaction_handler()
async def handle_transaction(t: Transaction, ctx: Context):
    """Handle transaction here"""
    ctx.wallet  # this way you can use QiwiWallet instance to avoid global variables


@dp.message_handler()
async def handle_message(msg: Message):
    await msg.answer(text='Hello world')


if __name__ == '__main__':
    executor.start_polling(wallet, qiwi_dp, AiogramPollingPlugin(dp))
