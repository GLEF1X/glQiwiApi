from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    MutableMapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from aiohttp import RequestInfo
from pydantic import BaseModel

from glQiwiApi import base_types
from glQiwiApi.qiwi.exceptions import APIError
from glQiwiApi.qiwi.types import TransactionType, Limit
from glQiwiApi.qiwi.types.transaction import History
from glQiwiApi.utils.dates_conversion import (
    datetime_to_iso8601_with_moscow_timezone,
)

try:
    import orjson
except (ModuleNotFoundError, ImportError):  # pragma: no cover # type: ignore
    import json as orjson  # type: ignore

Model = TypeVar("Model", bound=BaseModel)
DEFAULT_EXCLUDE = ("cls", "self", "__class__")


def filter_dictionary_none_values(dictionary: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Pop NoneType values and convert everything to str, designed?for=params

    :param dictionary: source dict
    :return: filtered dict
    """
    return {k: str(v) for k, v in dictionary.items() if v is not None}


def make_payload(**kwargs: Any) -> Dict[Any, Any]:
    return {
        key: value
        for key, value in kwargs.items()
        if key not in DEFAULT_EXCLUDE and value is not None
    }


def get_decoded_result(
    error_messages: Dict[int, str],
    status_code: int,
    request_info: RequestInfo,
    body: str,
) -> Dict[Any, Any]:
    """
    Checks whether `result` is a valid API response.
    A result is considered invalid if:
        - The server returned an HTTP response code other than 200

    :param error_messages:
    :param status_code: status code
    :param body: body of response
    :param request_info:
    :return: The result parsed to a JSON dictionary
    :raises ApiException: if one of the above listed cases is applicable
    """

    try:
        result_json = cast(Dict[Any, Any], orjson.loads(body))
    except ValueError:
        result_json = {}

    if status_code == HTTPStatus.OK:
        return result_json

    raise APIError(
        message=error_messages.get(status_code),
        status_code=status_code,
        request_data=request_info,
    )


def parse_auth_link(response_data: str) -> str:
    """
    Parse link for getting code, which needs to be entered in the method
    get_access_token

    :param response_data:
    """
    regexp = re.compile(
        r"https://yoomoney.ru/oauth2/authorize[?]requestid[=]\w+"
    )  # pragma: no cover
    return cast(str, re.findall(regexp, str(response_data))[0])  # pragma: no cover


def format_dates(
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    payload_data: Dict[Any, Any],
) -> Dict[Any, Any]:
    """Check correctness of transferred dates and add it to request"""
    if isinstance(start_date, datetime) and isinstance(end_date, datetime):
        if (end_date - start_date).total_seconds() > 0:
            payload_data.update(
                {
                    "startDate": datetime_to_iso8601_with_moscow_timezone(start_date),
                    "endDate": datetime_to_iso8601_with_moscow_timezone(end_date),
                }
            )
        else:
            raise ValueError("end_date cannot be bigger than start_date")
    return payload_data


def parse_commission_request_payload(
    default_data: base_types.WrappedRequestPayload,
    auth_maker: Callable[..., Any],
    pay_sum: Union[int, float],
    to_account: str,
) -> Tuple[base_types.WrappedRequestPayload, Union[str, None]]:
    """Set calc_commission payload"""
    payload = deepcopy(default_data)
    payload.headers = auth_maker(payload.headers)
    payload.json["purchaseTotals"]["total"]["amount"] = pay_sum
    payload.json["account"] = to_account
    return payload, "99" if len(to_account) <= 15 else None


def retrieve_card_data(
    default_data: base_types.WrappedRequestPayload,
    trans_sum: Union[int, float, str],
    to_card: str,
    auth_maker: Callable[..., Any],
) -> base_types.WrappedRequestPayload:
    """Set card data payload"""
    data = deepcopy(default_data)
    data.json["sum"]["amount"] = trans_sum
    data.json["fields"]["account"] = to_card
    data.headers = auth_maker(headers=data.headers)
    return data


def set_data_to_wallet(
    data: base_types.WrappedRequestPayload,
    to_number: str,
    trans_sum: Union[str, int, float],
    comment: Optional[str] = None,
    currency: Any = "643",
) -> base_types.WrappedRequestPayload:
    data.json["sum"]["amount"] = str(trans_sum)
    data.json["sum"]["currency"] = str(currency)
    data.json["fields"]["account"] = to_number
    if comment is not None:
        data.json["comment"] = comment
    return data


def patch_p2p_create_payload(
    wrapped_data: base_types.WrappedRequestPayload,
    amount: Union[str, int, float],
    life_time: str,
    comment: Optional[str] = None,
    theme_code: Optional[str] = None,
    pay_source_filter: Optional[List[str]] = None,
) -> Dict[MutableMapping[Any, Any], Any]:
    """Setting data for p2p form creation transfer"""
    wrapped_data.json["amount"]["value"] = str(amount)
    wrapped_data.json["comment"] = comment
    wrapped_data.json["expirationDateTime"] = life_time
    if isinstance(pay_source_filter, list):
        source_filters = " ".join(pay_source_filter).replace(" ", ",")
        wrapped_data.json["customFields"]["paySourcesFilter"] = source_filters
    if isinstance(theme_code, str):
        wrapped_data.json["customFields"]["themeCode"] = theme_code
    if not isinstance(theme_code, str) and pay_source_filter not in [  # type: ignore
        "qw",
        "card",
        "mobile",
    ]:
        wrapped_data.json.pop("customFields")
    return wrapped_data.json


def is_transaction_exists_in_history(
    history: History,
    amount: Union[int, float],
    transaction_type: TransactionType = TransactionType.IN,
    sender: Optional[str] = None,
    comment: Optional[str] = None,
) -> bool:
    for txn in history:
        if txn.sum.amount < amount or txn.type != transaction_type.value:
            continue
        if txn.comment == comment and txn.to_account == sender:
            return True
        elif comment and sender:
            continue
        elif txn.to_account == sender:
            return True
        elif sender:
            continue
        elif txn.comment == comment:
            return True
        elif comment:
            continue
        return True
    return False


def parse_iterable_to_list_of_objects(iterable: Iterable[Any], model: Type[Model]) -> List[Model]:
    """
    Parse simple objects, which cant raise ValidationError

    :param iterable:
    :param model: pydantic model, which will parse data
    """
    return [model.parse_obj(obj) for obj in iterable]


def get_qiwi_master_data(ph_number: str, data: Dict[Any, Any]) -> Dict[Any, Any]:
    payload = deepcopy(data)
    payload["fields"]["account"] = ph_number
    return payload


def get_new_card_data(ph_number: str, order_id: str, data: Dict[Any, Any]) -> Dict[Any, Any]:
    payload = deepcopy(data)
    payload["fields"].pop("vas_alias")
    payload["fields"].update(order_id=order_id)
    payload["fields"]["account"] = ph_number
    return payload


def parse_limits(response: Dict[Any, Any]) -> Dict[str, Limit]:
    resp_limits = cast(Dict[str, List[Dict[Any, Any]]], response["limits"])
    return {
        code: [Limit.parse_obj(limit) for limit in limits]  # type: ignore
        for code, limits in resp_limits.items()
    }


def check_dates_for_statistic_request(start_date: datetime, end_date: datetime) -> None:
    first_expression = isinstance(start_date, datetime) and isinstance(end_date, datetime)
    second_expression = isinstance(start_date, timedelta) and isinstance(end_date, datetime)
    if first_expression or second_expression:
        delta: timedelta = end_date - start_date
        if delta.days > 90:
            raise ValueError("The maximum period for downloading statistics is 90 calendar days.")
    else:
        raise ValueError("You passed in the start and end date values in the wrong format.")
