import concurrent.futures as futures
from typing import Union, TypeVar, Optional, Callable, Any, MutableMapping, \
    Dict, NewType

from .basics import (
    Type,
    Sum,
    Commission,
    OptionalSum
)
from .particular import (
    Response,
    WrapperData
)
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
    Restriction
)
from .yoomoney_types import (
    OperationType,
    OperationDetails,
    PreProcessPaymentResponse,
    Operation,
    Payment,
    IncomingTransaction,
    AccountInfo
)

ALL_TYPES = Union[
    Transaction, QiwiAccountInfo, Account, Limit,
    Bill, BillError, Statistic, Balance, Identification,
    AccountInfo, Operation, OperationDetails,
    PreProcessPaymentResponse, Payment, IncomingTransaction,
    Terminal, Partner
]

Executors = TypeVar(
    'Executors',
    futures.ThreadPoolExecutor,
    futures.ProcessPoolExecutor,
    Optional[None]
)

FuncT = TypeVar('FuncT', bound=Callable[..., Any])

MEMData = NewType('MEMData', MutableMapping[str, Dict[str, Any]])

N = TypeVar('N')

__all__ = (
    'QiwiAccountInfo',
    'Transaction',
    'Bill',
    'BillError',
    'P2PKeys',
    'Statistic',
    'Limit',
    'Account',
    'Identification',
    'Balance',
    'AccountInfo',
    'OperationType',
    'Operation',
    'OperationDetails',
    'PreProcessPaymentResponse',
    'Payment',
    'IncomingTransaction',
    'Response',
    'WrapperData',
    'Sum',
    'Type',
    'OptionalSum',
    'Commission',
    'ALL_TYPES',
    'PaymentInfo',
    'OrderDetails',
    'RefundBill',
    'Polygon',
    'Terminal',
    'Partner',
    'WebHookConfig',
    'WebHook',
    'Notification',
    'Executors',
    'FuncT',
    'MEMData',
    'N',
    'CrossRate',
    'FreePaymentDetailsFields',
    'PaymentMethod',
    'Card',
    'Restriction'
)
