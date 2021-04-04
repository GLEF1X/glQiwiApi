from typing import Union, Any, Callable, TypeVar

from glQiwiApi.data import Identification, AccountInfo, Operation, \
    OperationDetails, PreProcessPaymentResponse, Payment, IncomingTransaction, WrapperData
from glQiwiApi.data_models import Transaction, QiwiAccountInfo, Account, Limit, Bill, BillError, Statistic

BasicTypes = Union[
    Transaction, Identification, AccountInfo, Operation, OperationDetails,
    PreProcessPaymentResponse, Payment, IncomingTransaction
]

PydanticTypes = Union[
    Transaction, QiwiAccountInfo, Account, Limit, Bill, BillError, Statistic
]

F = TypeVar('F', bound=Callable[..., Any])

__all__ = ('BasicTypes', 'F', 'WrapperData', 'PydanticTypes')
