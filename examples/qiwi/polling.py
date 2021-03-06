from glQiwiApi import QiwiWrapper, types
from glQiwiApi.utils import executor

api_access_token = "your token"
phone_number = "your number"

wallet = QiwiWrapper(api_access_token=api_access_token, phone_number=phone_number)


@wallet.transaction_handler()
async def my_first_handler(update: types.Transaction):
    assert isinstance(update, types.Transaction)


def on_startup(wrapper: QiwiWrapper):
    wrapper.dispatcher.logger.info("This message logged on startup")


executor.start_polling(wallet, on_startup=on_startup, skip_updates=True)
