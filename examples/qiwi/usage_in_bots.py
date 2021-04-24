from typing import Union

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor

from glQiwiApi import QiwiWrapper, types as qiwi_types

wallet = QiwiWrapper(
    secret_p2p='YOUR_SECRET_P2P_TOKEN'
)

BOT_TOKEN = 'BOT_TOKEN'

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def create_payment(amount: Union[float, int] = 1) -> qiwi_types.Bill:
    async with wallet:
        return await wallet.create_p2p_bill(amount=amount)


@dp.message_handler(text='Хочу оплатить')
async def payment(message: types.Message, state: FSMContext):
    bill = await create_payment()
    await message.answer(
        text=f'Хорошо, вот ваш счёт для оплаты:\n {bill.pay_url}'
    )
    await state.set_state('payment')
    await state.update_data(bill=bill)


@dp.message_handler(state='payment', text='Оплатил')
async def successful_payment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        bill: qiwi_types.Bill = data.get('bill')
    status = await bill.check()
    if status:
        await message.answer('Вы успешно оплатили счет')
        await state.finish()
    else:
        await message.answer('Счет не оплачен')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
