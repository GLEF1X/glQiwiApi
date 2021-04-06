from typing import Union, TypeVar, Callable, Any

from .basics import *
from .particular import *
from .qiwi_types import *
from .yoomoney_types import *

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
