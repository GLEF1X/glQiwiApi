from glQiwiApi.qiwi.clients.maps.client import QiwiMaps
from glQiwiApi.qiwi.clients.p2p.client import QiwiP2PClient
from glQiwiApi.qiwi.clients.wallet.client import QiwiWallet
from glQiwiApi.qiwi.clients.wrapper import QiwiWrapper

from .core.cache import APIResponsesCacheInvalidationStrategy, InMemoryCacheStorage
from .core.cache.storage import CacheStorage
from .yoo_money import YooMoneyAPI


def default_cache_storage() -> CacheStorage:
    return InMemoryCacheStorage(invalidate_strategy=APIResponsesCacheInvalidationStrategy())


__version__ = '2.15'

__all__ = (
    # clients
    'YooMoneyAPI',
    'QiwiMaps',
    'QiwiWallet',
    'QiwiP2PClient',
    'QiwiWrapper',
    # other
    '__version__',
    'default_cache_storage',
)
