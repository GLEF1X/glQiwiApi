==================
Usage with aiogram
==================

### Without middleware:

.. code-block:: python
    from aiogram import Bot, Dispatcher, types
    from aiogram.contrib.fsm_storage.memory import MemoryStorage
    from aiogram.dispatcher import FSMContext
    from aiogram.utils import executor

    from glQiwiApi import QiwiP2PClient
    from glQiwiApi.qiwi.clients.p2p.types import Bill

    qiwi_p2p_client = QiwiP2PClient(secret_p2p="YOUR_SECRET_P2P_TOKEN")

    BOT_TOKEN = "BOT_TOKEN"

    bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)


    @dp.message_handler(text="I want to pay")
    async def handle_creation_of_payment(message: types.Message, state: FSMContext):
        async with qiwi_p2p_client:
            bill = await qiwi_p2p_client.create_p2p_bill(amount=1)
        await message.answer(text=f"Ok, here's your invoice:\n {bill.pay_url}")
        await state.set_state("payment")
        await state.update_data(bill=bill)


    @dp.message_handler(state="payment", text="I have paid this invoice")
    async def handle_successful_payment(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            bill: Bill = data.get("bill")

        if await qiwi_p2p_client.check_if_bill_was_paid(bill):
            await message.answer("You have successfully paid your invoice")
            await state.finish()
        else:
            await message.answer("Invoice was not paid")


    if __name__ == "__main__":
        executor.start_polling(dp, skip_updates=True)


### With middleware:

.. code-block:: python
    import asyncio
    import logging
    from typing import Dict, Any

    from aiogram import Bot, Dispatcher, types
    from aiogram.contrib.fsm_storage.memory import MemoryStorage
    from aiogram.dispatcher import FSMContext
    from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware
    from aiogram.types.base import TelegramObject

    from glQiwiApi import QiwiP2PClient
    from glQiwiApi.qiwi.clients.p2p.types import Bill

    BOT_TOKEN = "BOT TOKEN"


    class EnvironmentMiddleware(LifetimeControllerMiddleware):
        def __init__(self, qiwi_p2p_client: QiwiP2PClient):
            super().__init__()
            self._qiwi_p2p_client = qiwi_p2p_client

        async def pre_process(self, obj: TelegramObject, data: Dict[str, Any], *args: Any) -> None:
            data["qiwi_p2p_client"] = self._qiwi_p2p_client


    async def handle_creation_of_payment(
        message: types.Message, state: FSMContext, qiwi_p2p_client: QiwiP2PClient
    ):
        async with qiwi_p2p_client:
            bill = await qiwi_p2p_client.create_p2p_bill(amount=1)
        await message.answer(text=f"Ok, here's your invoice:\n {bill.pay_url}")
        await state.set_state("payment")
        await state.update_data(bill=bill)


    async def handle_successful_payment(
        message: types.Message, state: FSMContext, qiwi_p2p_client: QiwiP2PClient
    ):
        async with state.proxy() as data:
            bill: Bill = data.get("bill")

        if await qiwi_p2p_client.check_if_bill_was_paid(bill):
            await message.answer("You have successfully paid your invoice")
            await state.finish()
        else:
            await message.answer("Invoice was not paid")


    async def main():
        bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
        storage = MemoryStorage()
        dp = Dispatcher(bot, storage=storage)
        dp.middleware.setup(
            EnvironmentMiddleware(
                qiwi_p2p_client=QiwiP2PClient(
                    secret_p2p=""
                )
            )
        )

        dp.register_message_handler(handle_creation_of_payment, text="I want to pay")
        dp.register_message_handler(
            handle_successful_payment, state="payment", text="I have paid this invoice"
        )

        # start
        try:
            await dp.start_polling()
        finally:
            await dp.storage.close()
            await dp.storage.wait_closed()
            await bot.session.close()


    logging.basicConfig(level=logging.DEBUG)
    if __name__ == "__main__":
        asyncio.run(main())
