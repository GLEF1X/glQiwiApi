import asyncio
import pathlib
from asyncio import AbstractEventLoop
from datetime import datetime, timedelta
from typing import Any, Union, Optional, Dict, Type, List, MutableMapping, \
    Tuple, overload, Coroutine, Callable, NoReturn

from glQiwiApi import types


def measure_time(func: types.FuncT) -> types.FuncT: ...


def datetime_to_str_in_iso(obj: Union[None, datetime, timedelta],
                           yoo_money_format: bool = False) -> str: ...


def parse_auth_link(response_data: Union[str, bytes]) -> Optional[str]: ...


def check_dates(
        start_date: Optional[datetime],
        end_date: Optional[datetime],
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
        pay_source_filter: Optional[List[str]] = None
) -> Dict[MutableMapping, Any]: ...


def multiply_objects_parse(
        lst_of_objects: Union[List[str], Tuple[str, ...]],
        model: Type[types.N]
) -> List[types.N]: ...


def take_event_loop(set_debug: bool = False) -> AbstractEventLoop: ...


def hmac_key(
        key: Optional[Any],
        amount: types.OptionalSum,
        status: Any,
        bill_id: str,
        site_id: str
) -> str: ...


def hmac_for_transaction(
        webhook_key_base64: Optional[Any],
        amount: types.Sum,
        txn_type: str,
        account: str,
        txn_id: str,
        txn_hash: Optional[str]
) -> bool: ...


def simple_multiply_parse(lst_of_objects: Union[List[Union[dict, str]], dict],
                          model: Type[types.N]) -> List[types.N]: ...


def custom_load(data: Dict[Any, Any]) -> Dict[str, Any]: ...


def check_params(amount_: Union[int, float], amount: Union[int, float],
                 txn: types.OperationDetails,
                 transaction_type: str) -> bool: ...


def allow_response_code(status_code: Union[str, int]) -> Any: ...


def qiwi_master_data(ph_number: str, data: dict) -> dict: ...


def new_card_data(ph_number: str, order_id: str) -> Tuple[str, dict]: ...


def to_datetime(string_representation: str) -> datetime: ...


def sync_measure_time(func: types.FuncT) -> types.FuncT: ...


def run_forever_safe(loop: asyncio.AbstractEventLoop) -> None: ...


def safe_cancel(loop: asyncio.AbstractEventLoop) -> None: ...


def parse_amount(txn_type: str, txn: types.OperationDetails) -> Tuple[
    Union[int, float], str]: ...


def _await_sync(future: asyncio.Future, executor: types.Executors,
                loop: asyncio.AbstractEventLoop) -> Any: ...


def _cancel_future(loop: asyncio.AbstractEventLoop, future: asyncio.Future,
                   executor: types.Executors) -> None: ...


def _stop_loop(loop: asyncio.AbstractEventLoop) -> None: ...


@overload
def sync(
        func: types.FuncT,
        *args: object,
        **kwargs: object
) -> Any: ...


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
        func: Callable[[int, str, str, datetime, str, str], Coroutine[
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
            [
                Union[
                    datetime, timedelta
                ], Union[datetime, timedelta], str, Optional[List[str]]
            ],
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
            [str, str, str], Coroutine[Any, Any, str]
        ],
        *args: Any,
        **kwargs: Any
) -> str: ...


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


def async_as_sync(func: types.FuncT) -> types.FuncT: ...


def check_transaction(
        transactions: List[types.Transaction],
        amount: Union[int, float],
        transaction_type: str = 'IN',
        sender: Optional[str] = None,
        comment: Optional[str] = None
) -> bool: ...


def parse_limits(
        response: types.Response,
        model: Type[types.Limit]
) -> Dict[str, types.Limit]: ...


def override_error_messages(
        status_codes: Dict[int, Dict[str, str]]
) -> types.FuncT: ...


def check_api_method(api_method: str) -> NoReturn: ...


def check_dates_for_statistic_request(
        start_date: Union[datetime, timedelta],
        end_date: Union[datetime, timedelta]
) -> NoReturn: ...


def save_file(dir_path: Union[str, pathlib.Path], file_name: Optional[str],
              data: Any) -> Coroutine[Any, Any, int]: ...
