from .core import (
    AbstractBillHandler,
    AbstractTransactionHandler,
    AbstractTransactionWebhookHandler,
    BaseFilter,
    Handler,
    LambdaBasedFilter,
)
from .qiwi import QiwiMaps, QiwiWallet, QiwiP2PClient
from .yoo_money import YooMoneyAPI

try:
    import uvloop

    uvloop.install()  # pragma: no cover
except ImportError:
    pass

__version__ = "2.0.0b1"

__all__ = (
    # clients
    "QiwiWallet",
    "YooMoneyAPI",
    "QiwiP2PClient",
    "QiwiMaps",
    # class-based handlers and filters
    "AbstractBillHandler",
    "AbstractTransactionHandler",
    "AbstractTransactionWebhookHandler",
    "Handler",
    "LambdaBasedFilter",
    "BaseFilter",
    # other
    "__version__",
)
