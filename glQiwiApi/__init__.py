from glQiwiApi.qiwi.clients.wallet.client import QiwiWallet
from glQiwiApi.qiwi.clients.p2p.client import QiwiP2PClient
from glQiwiApi.qiwi.clients.maps.client import QiwiMaps
from .yoo_money import YooMoneyAPI

try:
    import uvloop

    uvloop.install()  # pragma: no cover
except ImportError:
    pass

__version__ = "2.0.0b1"

__all__ = (
    # clients
    "YooMoneyAPI",
    "QiwiMaps",
    "QiwiWallet",
    "QiwiP2PClient",
    # other
    "__version__",
)
