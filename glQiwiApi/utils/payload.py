from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import (
    Any,
    Union,
    Optional,
    Dict,
    Type,
    List,
    MutableMapping,
    Tuple,
    Iterable,
    cast,
    TypeVar,
)

from aiohttp import RequestInfo
from pydantic import BaseModel

from glQiwiApi import types
from glQiwiApi.utils.format_casts import datetime_to_iso8601, datetime_to_utc

try:
    import orjson
except (ModuleNotFoundError, ImportError):  # pragma: no cover # type: ignore
    import json as orjson  # type: ignore

from glQiwiApi.utils import exceptions

Model = TypeVar("Model", bound=BaseModel)
DEFAULT_EXCLUDE = ("cls", "self", "__class__")


def filter_none(dictionary: Dict[Any, Any]) -> Dict[Any, Any]:
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


def check_result(
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

    raise exceptions.APIError(
        message=error_messages.get(status_code),
        status_code=status_code,
        traceback_info=request_info,
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
                    "startDate": datetime_to_iso8601(start_date),
                    "endDate": datetime_to_iso8601(end_date),
                }
            )
        else:
            raise ValueError("end_date cannot be bigger than start_date")
    return payload_data


def parse_commission_request_payload(
        default_data: types.WrappedRequestPayload,
        auth_maker: types.FuncT,
        pay_sum: Union[int, float],
        to_account: str,
) -> Tuple[types.WrappedRequestPayload, Union[str, None]]:
    """Set calc_commission payload"""
    payload = deepcopy(default_data)
    payload.headers = auth_maker(payload.headers)
    payload.json["purchaseTotals"]["total"]["amount"] = pay_sum
    payload.json["account"] = to_account
    return payload, "99" if len(to_account) <= 15 else None


def retrieve_card_data(
        default_data: types.WrappedRequestPayload,
        trans_sum: Union[int, float, str],
        to_card: str,
        auth_maker: types.FuncT,
) -> types.WrappedRequestPayload:
    """Set card data payload"""
    data = deepcopy(default_data)
    data.json["sum"]["amount"] = trans_sum
    data.json["fields"]["account"] = to_card
    data.headers = auth_maker(headers=data.headers)
    return data


def retrieve_base_headers_for_yoomoney(
        content_json: bool = False, auth: bool = False
) -> Dict[Any, Any]:
    headers = {
        "Host": "yoomoney.ru",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    if content_json:
        headers.update({"Accept": "application/json"})
    if auth:
        headers.update({"Authorization": "Bearer {token}"})
    return headers


def set_data_to_wallet(
        data: types.WrappedRequestPayload,
        to_number: str,
        trans_sum: Union[str, int, float],
        comment: Optional[str] = None,
        currency: str = "643",
) -> types.WrappedRequestPayload:
    data.json["sum"]["amount"] = str(trans_sum)
    data.json["sum"]["currency"] = currency
    data.json["fields"]["account"] = to_number
    if comment is not None:
        data.json["comment"] = comment
    data.headers.update({"User-Agent": "Android v3.2.0 MKT"})
    return data


def patch_p2p_create_payload(
        wrapped_data: types.WrappedRequestPayload,
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


def parse_iterable_to_list_of_objects(
        iterable: Iterable[Any], model: Type[Model]
) -> List[Model]:
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


def get_new_card_data(
        ph_number: str, order_id: str, data: Dict[Any, Any]
) -> Dict[Any, Any]:
    payload = deepcopy(data)
    payload["fields"].pop("vas_alias")
    payload["fields"].update(order_id=order_id)
    payload["fields"]["account"] = ph_number
    return payload


def parse_amount(
        txn_type: str, txn: types.OperationDetails
) -> Tuple[Union[int, float], str]:
    transaction_type_in_lower = types.OperationType.DEPOSITION.value.lower()  # type: str
    if txn_type == transaction_type_in_lower:
        return txn.amount, txn.comment  # type: ignore
    else:
        return txn.amount_due, txn.message  # type: ignore


def check_params(
        amount_: Union[int, float],
        amount: Union[int, float],
        txn: types.OperationDetails,
        transaction_type: str,
) -> bool:
    return amount is not None and amount <= amount_ and txn.direction == transaction_type


def check_transaction(
        transactions: List[types.Transaction],
        amount: Union[int, float],
        transaction_type: types.TransactionType = types.TransactionType.IN,
        sender: Optional[str] = None,
        comment: Optional[str] = None,
) -> bool:
    for txn in transactions:
        if float(txn.sum.amount) >= amount and txn.type.value == transaction_type.value:
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
    return False


def parse_limits(response: Dict[Any, Any]) -> Dict[str, types.Limit]:
    resp_limits = cast(Dict[str, List[Dict[Any, Any]]], response["limits"])
    return {
        code: [types.Limit.parse_obj(limit) for limit in limits]  # type: ignore
        for code, limits in resp_limits.items()
    }


def check_api_method(api_method: str) -> None:
    if not isinstance(api_method, str):
        raise RuntimeError(
            f"Invalid type of api_method(must  be string)."
            f" Passed {type(api_method)}"
        )


def check_transactions_payload(
        data: Dict[Any, Any],
        records: int,
        operation_types: Optional[
            Union[List[types.OperationType], Tuple[types.OperationType, ...]]
        ] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        start_record: Optional[int] = None,
) -> Dict[Any, Any]:
    from glQiwiApi import InvalidPayload

    if records <= 0 or records > 100:
        raise InvalidPayload(
            "Invalid number of records."
            "The number of records that can be requested,"
            "be in the range from 1 to 100 inclusive"
        )
    if operation_types and all(
            isinstance(operation_type, types.OperationType)
            for operation_type in operation_types
    ):
        op_types = [operation_type.value for operation_type in operation_types]
        data.update({"type": " ".join(op_types)})

    if isinstance(start_record, int):
        if start_record < 0:
            raise InvalidPayload("start_record must be positive")
        data.update({"start_record": start_record})

    if start_date:
        if not isinstance(start_date, datetime):
            raise InvalidPayload("start_date must be datetime instance")
        data.update({"from": datetime_to_utc(start_date)})

    if end_date:
        if not isinstance(end_date, datetime):
            raise InvalidPayload("end_date must be datetime instance")
        data.update({"till": datetime_to_utc(end_date)})
    return data


def check_dates_for_statistic_request(start_date: datetime, end_date: datetime) -> None:
    first_expression = isinstance(start_date, datetime) and isinstance(
        end_date, datetime
    )
    second_expression = isinstance(start_date, timedelta) and isinstance(
        end_date, datetime
    )
    if first_expression or second_expression:
        delta: timedelta = end_date - start_date
        if delta.days > 90:
            raise ValueError(
                "The maximum period for downloading statistics is 90 calendar days."
            )
    else:
        raise ValueError(
            "You passed in the start and end date values in the wrong format."
        )
