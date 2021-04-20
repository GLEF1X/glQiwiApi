import asyncio
from datetime import datetime, timedelta
from typing import Any, Union, Optional, Dict, Type, List, MutableMapping, \
    Tuple, overload, Coroutine, Callable

from glQiwiApi import types


def measure_time(func: Any) -> None: ...


def datetime_to_str_in_iso(obj: datetime,
                           yoo_money_format: bool = False) -> str: ...


def format_objects_for_fill(data: dict, transfers: Dict[str, str]) -> dict: ...


def parse_auth_link(response_data: Union[str, bytes]) -> Optional[str]: ...


def parse_headers(content_json: bool = False, auth: bool = False) -> Dict[
    Any, Any]: ...


def set_data_to_wallet(data: types.WrapperData,
                       to_number: str,
                       trans_sum: Union[str, int, float],
                       comment: str,
                       currency: str = '643') -> types.WrapperData: ...


def set_data_p2p_create(
        wrapped_data: types.WrapperData,
        amount: Union[str, int, float],
        life_time: str,
        comment: Optional[str] = None,
        theme_code: Optional[str] = None,
        pay_source_filter: Optional[str] = None
) -> Dict[MutableMapping, Any]: ...


def multiply_objects_parse(
        lst_of_objects: Union[List[str], Tuple[str, ...]],
        model: Type[types.PydanticTypes]
) -> List[types.PydanticTypes]: ...


def dump_response(func: Any) -> Any: ...


def simple_multiply_parse(lst_of_objects: Union[List[Union[dict, str]], dict],
                          model: Type[types.PydanticTypes]) -> List[
    types.PydanticTypes]: ...


def custom_load(data: Dict[Any, Any]) -> Dict[str, Any]: ...


def check_params(amount_: Union[int, float], amount: Union[int, float],
                 txn: types.OperationDetails, transaction_type: str) -> bool: ...


def allow_response_code(status_code: Union[str, int]) -> Any: ...


def qiwi_master_data(ph_number: str) -> Tuple[str, dict]: ...


def new_card_data(ph_number: str, order_id: str) -> Tuple[str, dict]: ...


def to_datetime(string_representation: str) -> datetime: ...


def sync_measure_time(func: Any) -> Any: ...


def _run_forever_safe(loop: asyncio.AbstractEventLoop) -> None: ...


def parse_amount(txn_type: str, txn: types.OperationDetails) -> Tuple[
    Union[int, float], str]: ...


def _await_sync(future: asyncio.Future, executor: types.E,
                loop: asyncio.AbstractEventLoop) -> Any: ...


def _cancel_future(loop: asyncio.AbstractEventLoop, future: asyncio.Future,
                   executor: types.E) -> None: ...


def _stop_loop(loop: asyncio.AbstractEventLoop) -> None: ...


def sync(
        func: types.FuncT,
        *args: object,
        **kwargs: object) -> Any: ...


@overload
def sync(
        func: Callable[
            [str, str, str, str, str, str, str, str], Coroutine[
                Any, Any, Optional[Dict[str, bool]]
            ]
        ],
        *args: Any,
        **kwargs: Any
) -> Optional[Dict[str, bool]]: ...


@overload
def sync(
        func: Callable[[Union[float, int], str], Coroutine[
            Any, Any, Union[types.Response, str]]],
        *args: Any,
        **kwargs: Any
) -> Union[types.Response, str]: ...


@overload
def sync(
        func: Callable[[], Coroutine[Any, Any, types.Sum]],
        *args: Any,
        **kwargs: Any
) -> types.Sum: ...


@overload
def sync(
        func: Callable[
            [int, str, Optional[datetime], Optional[datetime]], Coroutine[
                Any, Any, List[types.Transaction]
            ]
        ],
        *args: Any,
        **kwargs: Any
) -> List[types.Transaction]: ...


@overload
def sync(
        func: Callable[
            [str, Union[str, float, int], str, str], Coroutine[
                Any, Any, Union[str, types.Response]]
        ],
        *args: Any,
        **kwargs: Any
) -> Union[str, types.Response]: ...


@overload
def sync(
        func: Callable[[Union[str, int], str], Coroutine[
            Any, Any, types.Transaction]
        ],
        *args: Any,
        **kwargs: Any
) -> types.Transaction: ...


@overload
def sync(
        func: Callable[[], Coroutine[Any, Any, Union[
            List[Dict[str, str]], Exception
        ]]],
        *args: Any,
        **kwargs: Any
) -> Union[
    List[Dict[str, str]], Exception
]: ...


@overload
def sync(
        func: Callable[[], Coroutine[Any, Any, types.Identification]],
        *args: Any,
        **kwargs: Any
) -> types.Identification: ...


@overload
def sync(
        func: Callable[
            [
                Union[int, float],
                str,
                Optional[str],
                int,
                Optional[str]
            ],
            Coroutine[Any, Any, bool]
        ],
        *args: Any,
        **kwargs: Any
) -> bool: ...


@overload
def sync(
        func: Callable[[], Coroutine[Any, Any, Dict[str, types.Limit]]],
        *args: Any,
        **kwargs: Any
) -> Dict[str, types.Limit]: ...


@overload
def sync(
        func: Callable[[int], Coroutine[Any, Any, List[types.Bill]]],
        *args: Any,
        **kwargs: Any
) -> List[types.Bill]: ...


@overload
def sync(
        func: Callable[[int, ...], Coroutine[
            Any, Any, Union[types.Bill, types.BillError]]],
        *args: Any,
        **kwargs: Any
) -> Union[types.Bill, types.BillError]: ...


@overload
def sync(
        func: Callable[[str], Coroutine[Any, Any, types.Bill]],
        *args: Any,
        **kwargs: Any
) -> types.Bill: ...


@overload
def sync(
        func: Callable[[Union[str, int], str, Optional[str]], Coroutine[
            Any, Any, Union[bytearray, int]]
        ],
        *args: Any,
        **kwargs: Any
) -> Union[bytearray, int]: ...


@overload
def sync(
        func: Callable[
            [str, Union[int, float]], Coroutine[Any, Any, types.Commission]],
        *args: Any,
        **kwargs: Any
) -> types.Commission: ...


@overload
def sync(
        func: Callable[
            [], Coroutine[Any, Any, types.QiwiAccountInfo]],
        *args: Any,
        **kwargs: Any
) -> types.QiwiAccountInfo: ...


@overload
def sync(
        func: Callable[
            [Union[datetime, timedelta], Union[datetime, timedelta], str, ...],
            Coroutine[Any, Any, types.Statistic]],
        *args: Any,
        **kwargs: Any
) -> types.Statistic: ...


@overload
def sync(
        func: Callable[
            [], Coroutine[Any, Any, List[types.Account]]],
        *args: Any,
        **kwargs: Any
) -> List[types.Account]: ...


@overload
def sync(
        func: Callable[
            [str], Coroutine[Any, Any, Optional[Dict[str, bool]]]],
        *args: Any,
        **kwargs: Any
) -> Optional[Dict[str, bool]]: ...


@overload
def sync(
        func: Callable[
            [], Coroutine[Any, Any, List[types.Balance]]],
        *args: Any,
        **kwargs: Any
) -> List[types.Balance]: ...


@overload
def sync(
        func: Callable[
            [Union[str, int], Union[str, int],
             Union[types.OptionalSum, Dict[str, Union[str, int]]]
             ], Coroutine[Any, Any, types.RefundBill]],
        *args: Any,
        **kwargs: Any
) -> types.RefundBill: ...


@overload
def sync(
        func: Callable[
            [], Coroutine[Any, Any, types.PaymentInfo]],
        *args: Any,
        **kwargs: Any
) -> types.PaymentInfo: ...


@overload
def sync(
        func: Callable[
            [str], Coroutine[Any, Any, types.OrderDetails]],
        *args: Any,
        **kwargs: Any
) -> types.OrderDetails: ...


@overload
def sync(
        func: Callable[
            [List[str], str, str], Coroutine[Any, Any, str]],
        *args: Any,
        **kwargs: Any
) -> str: ...


@overload
def sync(
        func: Callable[
            [str, str, str], Coroutine[Any, Any, str]],
        *args: Any,
        **kwargs: Any
) -> str: ...


@overload
def sync(
        func: Callable[
            [], Coroutine[Any, Any, Optional[Dict[str, bool]]]],
        *args: Any,
        **kwargs: Any
) -> Optional[Dict[str, bool]]: ...


@overload
def sync(
        func: Callable[
            [], Coroutine[Any, Any, types.AccountInfo]],
        *args: Any,
        **kwargs: Any
) -> types.AccountInfo: ...


@overload
def sync(
        func: Callable[
            [Optional[
                 Union[
                     List[types.OperationType], Tuple[
                         types.OperationType, ...]
                 ]
             ],
             Optional[datetime], Optional[datetime], Optional[int], int,
             Optional[Union[str, int]]
             ], Coroutine[Any, Any, List[types.Operation]]],
        *args: Any,
        **kwargs: Any
) -> List[types.Operation]: ...


@overload
def sync(
        func: Callable[
            [str], Coroutine[Any, Any, types.OperationDetails]],
        *args: Any,
        **kwargs: Any
) -> types.OperationDetails: ...


@overload
def sync(
        func: Callable[
            [
                str, Union[int, float], str, str, str, Optional[str],
                bool, Optional[str], Optional[str], int
            ], Coroutine[Any, Any, types.Payment]],
        *args: Any,
        **kwargs: Any
) -> types.Payment: ...


@overload
def sync(
        func: Callable[
            [Optional[None]], Coroutine[
                Any, Any, Optional[Union[float, int]]]],
        *args: Any,
        **kwargs: Any
) -> Optional[Union[float, int]]: ...


@overload
def sync(
        func: Callable[
            [str, str], Coroutine[Any, Any, types.IncomingTransaction]],
        *args: Any,
        **kwargs: Any
) -> types.IncomingTransaction: ...


@overload
def sync(
        func: Callable[
            [str], Coroutine[Any, Any, Dict[str, str]]
        ],
        *args: Any,
        **kwargs: Any
) -> Dict[str, str]: ...


@overload
def sync(
        func: Callable[
            [
                Union[int, float], str, Optional[str],
                int, Optional[str]
            ], Coroutine[Any, Any, bool]
        ],
        *args: Any,
        **kwargs: Any
) -> bool: ...
