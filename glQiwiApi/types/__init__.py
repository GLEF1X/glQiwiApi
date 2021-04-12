from typing import Union

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
    OperationType,
    OperationDetails,
    PreProcessPaymentResponse,
    Operation,
    Payment,
    IncomingTransaction,
    AccountInfo
)

BasicTypes = Union[
    AccountInfo, Operation, OperationDetails,
    PreProcessPaymentResponse, Payment, IncomingTransaction
]

PydanticTypes = Union[
    Transaction, QiwiAccountInfo, Account, Limit,
    Bill, BillError, Statistic, Balance, Identification
]

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
    'BasicTypes',
    'PydanticTypes'
]
