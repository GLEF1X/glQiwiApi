import asyncio

from glQiwiApi import QiwiWrapper

# Кэширование по умолчанию отключено, так как
# эта функция все ещё находиться в бета тестировании и
# константа DEFAULT_CACHE_TIME = 0, чтобы это исправить и включить кэширование
# нужно передать cache_time в конструктор класса QiwiWrapper
# или YooMoneyAPI
wallet = QiwiWrapper(
    # Токен, полученный с https://qiwi.com/api
    api_access_token='token',
    # Номер вашего мобильного номера с "+"
    phone_number='+phone_number',
    # Время кэширование запроса в секундах(пока ещё в бета тестировании)
    cache_time=5
)


async def cache_test():
    async with wallet:
        # Результат заноситься в кэш
        print(await wallet.transactions(rows_num=50))
        # Этот запрос возьмется из кэша
        print(await wallet.transactions(rows_num=50))

        # Запросы ниже не будут браться из кэша,
        # причиной тому есть разница в параметрах запроса
        # Результат все также заноситься в кэш
        print(len(await wallet.transactions(rows_num=30)) == 30)
        # Однако, повторный запрос к апи будет выполнен, поскольку
        # при попытке взятие результата из кэша валидатор сравнивает
        # параметры запроса, если они не совпадают, то
        # кэш игнорируется
        # Повторный запрос к апи
        print(len(await wallet.transactions(rows_num=10)) == 10)


asyncio.run(cache_test())
