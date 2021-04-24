import asyncio
from datetime import datetime, timedelta
from typing import Any, Union, Optional, Dict, Type, List, MutableMapping, \
    Tuple, overload, Coroutine, Callable

from glQiwiApi import types


def measure_time(func: Any) -> None: ...


def datetime_to_str_in_iso(obj: datetime,
                           yoo_money_format: bool = False) -> str: ...


def parse_auth_link(response_data: Union[str, bytes]) -> Optional[str]: ...


def check_dates(
        start_date: Union[datetime, timedelta],
        end_date: Union[datetime, timedelta],
        payload_data: dict
) -> dict: ...


def parse_commission_request_payload(
        default_data: types.WrapperData,
        auth_maker: types.FuncT,
        pay_sum: Union[int, float],
        to_account: str
) -> Tuple[types.WrapperData, Union[str, None]]: ...


def parse_card_data(
        default_data: types.WrapperData,
        trans_sum: Union[int, float, str],
        to_card: str,
        auth_maker: types.FuncT
) -> types.WrapperData: ...


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


def hmac_key(
        key: str,
        amount: types.OptionalSum,
        status: Any,
        bill_id: str,
        site_id: str
) -> str: ...


def hmac_for_transaction(
        webhook_key_base64: str,
        amount: types.Sum,
        txn_type: str,
        account: str,
        txn_id: str,
        txn_hash: str
) -> bool: ...


def simple_multiply_parse(lst_of_objects: Union[List[Union[dict, str]], dict],
                          model: Type[types.PydanticTypes]) -> List[
    types.PydanticTypes]: ...


def custom_load(data: Dict[Any, Any]) -> Dict[str, Any]: ...


def check_params(amount_: Union[int, float], amount: Union[int, float],
                 txn: types.OperationDetails,
                 transaction_type: str) -> bool: ...


def allow_response_code(status_code: Union[str, int]) -> Any: ...


def qiwi_master_data(ph_number: str) -> Tuple[str, dict]: ...


def new_card_data(ph_number: str, order_id: str) -> Tuple[str, dict]: ...


def to_datetime(string_representation: str) -> datetime: ...


def sync_measure_time(func: Any) -> Any: ...


def _run_forever_safe(loop: asyncio.AbstractEventLoop) -> None: ...


def parse_amount(txn_type: str, txn: types.OperationDetails) -> Tuple[
    Union[int, float], str]: ...


def _await_sync(future: asyncio.Future, executor: types.Executors,
                loop: asyncio.AbstractEventLoop) -> Any: ...


def _cancel_future(loop: asyncio.AbstractEventLoop, future: asyncio.Future,
                   executor: types.Executors) -> None: ...


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
        func: Callable[[Optional[None]], Coroutine[Any, Any, types.Sum]],
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
        func: Callable[[Optional[None]], Coroutine[Any, Any, Union[
            List[Dict[str, str]], Exception
        ]]],
        *args: Any,
        **kwargs: Any
) -> Union[
    List[Dict[str, str]], Exception
]: ...


@overload
def sync(
        func: Callable[
            [Optional[None]], Coroutine[Any, Any, types.Identification]],
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
            [Optional[None]], Coroutine[Any, Any, types.QiwiAccountInfo]],
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
            [Optional[None]], Coroutine[Any, Any, List[types.Account]]],
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
            [Optional[None]], Coroutine[Any, Any, List[types.Balance]]],
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
            [Optional[None]], Coroutine[Any, Any, types.PaymentInfo]],
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
            [Optional[None]], Coroutine[Any, Any, Optional[Dict[str, bool]]]],
        *args: Any,
        **kwargs: Any
) -> Optional[Dict[str, bool]]: ...


@overload
def sync(
        func: Callable[
            [Optional[None]], Coroutine[Any, Any, types.AccountInfo]],
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


@overload
def sync(
        func: Callable[
            [Optional[None]], Coroutine[Any, Any, List[types.Partner]]
        ],
        *args: Any,
        **kwargs: Any
) -> List[types.Partner]: ...


@overload
def sync(
        func: Callable[
            [
                types.Polygon, int, int, bool, list,
                bool, bool, int, list
            ], Coroutine[Any, Any, List[types.Terminal]]
        ],
        *args: Any,
        **kwargs: Any
) -> List[types.Terminal]: ...


@overload
def sync(
        func: Callable[
            [
                Optional[str], int, bool, bool
            ], Coroutine[Any, Any, Tuple[types.WebHookConfig, str]]
        ]
) -> Tuple[types.WebHookConfig, str]: ...


@overload
def sync(
        func: types.FuncT,
        *args: Any,
        **kwargs: Any
) -> Any: ...
