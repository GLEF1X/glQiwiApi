import datetime

from glQiwiApi import QiwiWrapper, execute_async_as_sync

TOKEN = "Api token from https://qiwi.com/api"
WALLET = "+phone_number"

# As always, we create an instance of the class,
# but pass on "without_context" as True
wallet = QiwiWrapper(api_access_token=TOKEN, phone_number=WALLET)


def sync_function() -> None:
    start_date = datetime.datetime.now() - datetime.timedelta(days=5)
    # Use the sync () function and pass the function we want to execute
    # without calling it, that is, pass it as a regular variable
    result = execute_async_as_sync(
        wallet.history,
        rows_num=50,
        start_date=start_date,
        end_date=datetime.datetime.now(),
    )
    print(result)


sync_function()
