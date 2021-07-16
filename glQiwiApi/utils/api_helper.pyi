import asyncio
import logging
import pathlib
from asyncio import AbstractEventLoop
from concurrent.futures import Future
from datetime import datetime, timedelta
from typing import (
    Any,
    Union,
    Optional,
    Dict,
    Type,
    List,
    MutableMapping,
    Tuple,
    Coroutine,
    NoReturn,
    Iterable,
    Callable,
    TypeVar,
    Awaitable,
)

from aiohttp import RequestInfo

from glQiwiApi import types

class_ = TypeVar("class_", bound="allow_response_code")

def check_result(
    error_messages: Optional[Dict[int, str]],
    content_type: str,
    status_code: int,
    request_info: RequestInfo,
    body: str,
) -> Dict[Any, Any]: ...

class measure_time(object):  # NOQA
    _logger: Union[logging.Logger, None] = None
    def __init__(self, logger: Union[logging.Logger, None] = None) -> None: ...
    def __call__(self, func: types.N) -> types.N: ...
    def _log(self, msg: str, *args: Any) -> None: ...

def datetime_to_str_in_iso(
    obj: Union[None, datetime, timedelta], yoo_money_format: bool = False
) -> str: ...
def parse_auth_link(response_data: str) -> Optional[str]: ...
def check_dates(
    start_date: Optional[datetime], end_date: Optional[datetime], payload_data: Dict[Any, Any]
) -> Dict[Any, Any]: ...
def parse_commission_request_payload(
    default_data: types.WrapperData,
    auth_maker: types.FuncT,
    pay_sum: Union[int, float],
    to_account: str,
) -> Tuple[types.WrapperData, Union[str, None]]: ...
def parse_card_data(
    default_data: types.WrapperData,
    trans_sum: Union[int, float, str],
    to_card: str,
    auth_maker: types.FuncT,
) -> types.WrapperData: ...
def parse_headers(content_json: bool = False, auth: bool = False) -> Dict[Any, Any]: ...
def set_data_to_wallet(
    data: types.WrapperData,
    to_number: str,
    trans_sum: Union[str, int, float],
    comment: str,
    currency: str = "643",
) -> types.WrapperData: ...
def set_data_p2p_create(
    wrapped_data: types.WrapperData,
    amount: Union[str, int, float],
    life_time: str,
    comment: Optional[str] = None,
    theme_code: Optional[str] = None,
    pay_source_filter: Optional[List[str]] = None,
) -> Dict[MutableMapping[Any, Any], Any]: ...
def multiply_objects_parse(
    lst_of_objects: Union[List[str], Tuple[str, ...]], model: Type[types.N]
) -> List[types.N]: ...
def take_event_loop(set_debug: bool = False) -> AbstractEventLoop: ...
def hmac_key(
    key: Optional[Any],
    amount: types.OptionalSum,
    status: Any,
    bill_id: str,
    site_id: str,
) -> str: ...
def hmac_for_transaction(
    webhook_key_base64: Optional[Any],
    amount: types.Sum,
    txn_type: str,
    account: str,
    txn_id: str,
    txn_hash: Optional[str],
) -> bool: ...
def simple_multiply_parse(
    objects: Iterable[Any], model: Type[types.N]
) -> List[types.N]: ...
def custom_load(data: Dict[Any, Any]) -> Dict[str, Any]: ...
def check_params(
    amount_: Union[int, float],
    amount: Union[int, float],
    txn: types.OperationDetails,
    transaction_type: str,
) -> bool: ...

class allow_response_code:  # NOQA
    status_code: int
    def __init__(self, status_code: int) -> None: ...
    def __call__(self: class_, func: types.N) -> types.N: ...

def qiwi_master_data(ph_number: str, data: Dict[Any, Any]) -> Dict[Any, Any]: ...
def new_card_data(ph_number: str, order_id: str) -> Dict[Any, Any]: ...
def to_datetime(string_representation: str) -> datetime: ...
def run_forever_safe(loop: asyncio.AbstractEventLoop, callback: Optional[Callable[..., Awaitable[types.N]]]) -> None: ...
def safe_cancel(loop: asyncio.AbstractEventLoop, callback: Optional[Callable[..., Awaitable[types.N]]]) -> None: ...
def parse_amount(
    txn_type: str, txn: types.OperationDetails
) -> Tuple[Union[int, float], str]: ...
def _cancel_future(
    loop: asyncio.AbstractEventLoop, future: asyncio.Future[types.N], executor: types.Executors
) -> None: ...
def _stop_loop(loop: asyncio.AbstractEventLoop) -> None: ...
def await_sync(future: Future[types.N]) -> types.N: ...
def sync(
    func: Callable[..., Coroutine[Any, Any, types.N]], *args: object, **kwargs: object
) -> types.N: ...

class async_as_sync:  # NOQA
    _shutdown_callback: Callable[..., Awaitable[types.N]]
    def __init__(
        self, shutdown_callback: Optional[Callable[..., Awaitable[types.N]]] = None
    ) -> None: ...
    def __call__(
        self, func: Callable[..., Coroutine[Any, Any, types.N]]
    ) -> Callable[..., types.N]: ...

def check_transaction(
    transactions: List[types.Transaction],
    amount: Union[int, float],
    transaction_type: str = "IN",
    sender: Optional[str] = None,
    comment: Optional[str] = None,
) -> bool: ...
def parse_limits(
    response: Dict[Any, Any], model: Type[types.Limit]
) -> Dict[str, types.Limit]: ...

class override_error_messages:  # NOQA
    status_codes: Dict[int, Dict[str, str]]
    def __init__(self, status_codes: Dict[int, Dict[str, str]]): ...
    def __call__(self, func: types.N) -> types.N: ...

def check_api_method(api_method: str) -> NoReturn: ...
def check_transactions_payload(
    data: Dict[Any, Any],
    records: int,
    operation_types: Optional[
        Union[List[types.OperationType], Tuple[types.OperationType, ...]]
    ] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    start_record: Optional[int] = None,
) -> Dict[Any, Any]: ...
def check_dates_for_statistic_request(
    start_date: Union[datetime, timedelta], end_date: Union[datetime, timedelta]
) -> NoReturn: ...
async def save_file(
    dir_path: Union[str, pathlib.Path, None], file_name: Optional[str], data: Any
) -> Union[int, bytes]: ...
