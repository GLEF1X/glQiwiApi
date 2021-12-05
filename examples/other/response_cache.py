import asyncio

from glQiwiApi import QiwiWrapper

# Caching is disabled by default because
# this feature is still in beta testing and
# constant DEFAULT_CACHE_TIME = 0 to fix this and enable caching
# you need to pass cache_time to the constructor of the QiwiWrapper class
# or YooMoneyAPI
wallet = QiwiWrapper(
    # QIWI API token from https://qiwi.com/api
    api_access_token="token",
    # phone number startswith "+"
    phone_number="+phone_number",
    # Cache time in seconds
    cache_time_in_seconds=5,
)


async def cache_test():
    async with wallet:
        # The result will be cached
        print(await wallet.transactions(rows=40))
        # The result will be taken from cache
        print(await wallet.transactions(rows=40))

        # The requests below will not be taken from the cache,
        # the reason for this is the difference in the request parameters
        # The result is also stored in the cache
        print(len(await wallet.transactions(rows=30)) == 30)  # True
        # However, a second request to the api will be executed, because
        # when trying to retrieve a result from the cache, the validator compares
        # request parameters, if they do not match, then
        # cache is ignored
        # Repeated request to api
        print(len(await wallet.transactions(rows=10)) == 10)  # True


asyncio.run(cache_test())
