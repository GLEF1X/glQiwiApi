from typing import Union, Any, Callable, TypeVar

from glQiwiApi.data import Transaction, Commission, Bill, Limit, Identification, AccountInfo, Operation, \
    OperationDetails, PreProcessPaymentResponse, Payment, IncomingTransaction

BasicTypes = Union[Transaction, Identification, Limit, Bill, Commission, AccountInfo, Operation, OperationDetails,
                   PreProcessPaymentResponse, Payment, IncomingTransaction]
F = TypeVar('F', bound=Callable[..., Any])

__all__ = ('BasicTypes', 'F')
