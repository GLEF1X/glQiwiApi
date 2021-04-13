import asyncio

from glQiwiApi import QiwiWrapper

# Кэширование по умолчанию отключено, так как
# эта функция все ещё находиться в бета тестировании и
# константа DEFAULT_CACHE_TIME = 0, чтобы это исправить и включить кэширование
# нужно передать cache_time в конструктор класса QiwiWrapper
# или YooMoneyAPI
wallet = QiwiWrapper(
    api_access_token='token',  # Токен, полученный с https://qiwi.com/api
    phone_number='+phone_number',  # Номер вашего мобильного номера с "+"
    cache_time=5  # Время кэширование запроса в секундах(пока ещё в бета тестировании)
)


async def cache_test():
    async with wallet:
        print(await wallet.transactions(rows_num=50))  # Результат заноситься в кэш
        print(await wallet.transactions(rows_num=50))  # Этот запрос возьмется из кэша

        # Такие запросы не будут браться из кэша,
        # причиной тому есть разница в параметрах запроса
        print(len(await wallet.transactions(rows_num=30)) == 30)  # Результат все также заноситься в кэш
        # Однако, повторный запрос к апи будет выполнен, поскольку
        # при попытке взятие результата из кэша валидатор сравнивает
        # параметры запроса, если они не совпадают, то
        # кэш игнорируется
        print(len(await wallet.transactions(rows_num=10)) == 10)  # Повторный запрос к апи


asyncio.run(cache_test())
