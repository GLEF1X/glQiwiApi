from typing import Union, TypeVar, Callable, Any

from .basics import (
    Type, Sum, Commission, OptionalSum
)
from .particular import (Response, ProxyService, WrapperData, proxy_list)
from .qiwi_types import (
    Bill,
    BillError,
    Statistic,
    Balance,
    Identification,
    Limit,
    Account,
    QiwiAccountInfo,
    Transaction
)
from .yoomoney_types import (
    OperationType, OperationDetails, PreProcessPaymentResponse, Operation, Payment, IncomingTransaction, AccountInfo,
    ALL_OPERATION_TYPES
)

BasicTypes = Union[
    AccountInfo, Operation, OperationDetails,
    PreProcessPaymentResponse, Payment, IncomingTransaction
]

PydanticTypes = Union[
    Transaction, QiwiAccountInfo, Account, Limit,
    Bill, BillError, Statistic, Balance, Identification
]

F = TypeVar('F', bound=Callable[..., Any])
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
    'ALL_OPERATION_TYPES',
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
    'BasicTypes',
    'F',
    'PydanticTypes'
]
