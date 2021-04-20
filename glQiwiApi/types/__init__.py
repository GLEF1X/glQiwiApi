import concurrent.futures as futures
from typing import Union, TypeVar, Optional, Callable, Any

from .basics import (
    Type,
    Sum,
    Commission,
    OptionalSum
)
from .particular import (
    Response,
    ProxyService,
    WrapperData,
    proxy_list
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
    Partner
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

PydanticTypes = Union[
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

__all__ = [
    'QiwiAccountInfo',
    'Transaction',
    'Bill',
    'BillError',
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
    'ProxyService',
    'proxy_list',
    'Sum',
    'Type',
    'OptionalSum',
    'Commission',
    'PydanticTypes',
    'PaymentInfo',
    'OrderDetails',
    'RefundBill',
    'Polygon',
    'Terminal',
    'Partner',
    'Executors',
    'FuncT'
]
