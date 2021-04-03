from typing import Union, Any, Callable, TypeVar

from glQiwiApi.data import Identification, AccountInfo, Operation, \
    OperationDetails, PreProcessPaymentResponse, Payment, IncomingTransaction, WrapperData
from glQiwiApi.models import Transaction, QiwiAccountInfo, Account, Limit, Bill, BillError, Statistic

BasicTypes = Union[
    Transaction, Identification, AccountInfo, Operation, OperationDetails,
    PreProcessPaymentResponse, Payment, IncomingTransaction, Account, Limit, Bill, BillError, Statistic
]

PydanticTypes = Union[Transaction, QiwiAccountInfo]

F = TypeVar('F', bound=Callable[..., Any])

__all__ = ('BasicTypes', 'F', 'WrapperData')
