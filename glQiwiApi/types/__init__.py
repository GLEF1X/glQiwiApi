import concurrent.futures as futures
from typing import Union, TypeVar, Optional, Callable, Any

from .basics import Type, Sum, OptionalSum
from .particular import Response, WrapperData
from .qiwi_types import (
    Bill,
    BillError,
    Statistic,
    Balance,
    Identification,
    Limit,
    Account,
    QiwiAccountInfo,
    Transaction,
    PaymentInfo,
    OrderDetails,
    RefundBill,
    Polygon,
    Terminal,
    Partner,
    WebHookConfig,
    WebHook,
    Notification,
    P2PKeys,
    CrossRate,
    FreePaymentDetailsFields,
    PaymentMethod,
    Card,
    Restriction,
    Commission,
    InvoiceStatus,
    TransactionType
)
from .yoomoney_types import (
    OperationType,
    OperationDetails,
    PreProcessPaymentResponse,
    Operation,
    Payment,
    IncomingTransaction,
    AccountInfo,
)

ALL_TYPES = Union[
    QiwiAccountInfo,
    Transaction,
    Bill,
    BillError,
    P2PKeys,
    Statistic,
    Limit,
    Account,
    Identification,
    Balance,
    AccountInfo,
    Operation,
    OperationDetails,
    PreProcessPaymentResponse,
    Payment,
    IncomingTransaction,
    Commission,
    PaymentInfo,
    OrderDetails,
    RefundBill,
    Polygon,
    Terminal,
    Partner,
    WebHookConfig,
    WebHook,
    Notification,
    CrossRate,
    FreePaymentDetailsFields,
    PaymentMethod,
    Card,
    Restriction,
    InvoiceStatus
]

AnyExecutor = TypeVar("AnyExecutor", futures.ThreadPoolExecutor, futures.ProcessPoolExecutor, Optional[None])

FuncT = TypeVar("FuncT", bound=Callable[..., Any])

N = TypeVar("N")

__all__ = (
    "QiwiAccountInfo",
    "Transaction",
    "Bill",
    "BillError",
    "P2PKeys",
    "InvoiceStatus",
    "Statistic",
    "Limit",
    "Account",
    "Identification",
    "Balance",
    "AccountInfo",
    "OperationType",
    "Operation",
    "OperationDetails",
    "PreProcessPaymentResponse",
    "Payment",
    "IncomingTransaction",
    "Response",
    "WrapperData",
    "Sum",
    "Type",
    "OptionalSum",
    "Commission",
    "ALL_TYPES",
    "PaymentInfo",
    "OrderDetails",
    "RefundBill",
    "Polygon",
    "Terminal",
    "Partner",
    "WebHookConfig",
    "WebHook",
    "Notification",
    "AnyExecutor",
    "FuncT",
    "N",
    "CrossRate",
    "FreePaymentDetailsFields",
    "PaymentMethod",
    "Card",
    "Restriction",
    "TransactionType"
)
