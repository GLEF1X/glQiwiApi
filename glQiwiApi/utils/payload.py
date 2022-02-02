import re
from http import HTTPStatus
from typing import (
    Any,
    Dict,
    Optional,
    TypeVar,
    Union,
    cast,
)

from pydantic import BaseModel

from glQiwiApi.core.session.holder import Response
from glQiwiApi.qiwi.clients.wallet.types.transaction import TransactionType, History
from glQiwiApi.qiwi.exceptions import QiwiAPIError

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
    exclude_list = kwargs.pop("exclude", ())
    return {
        key: value
        for key, value in kwargs.items()
        if key not in DEFAULT_EXCLUDE + exclude_list and value is not None
    }


def decode_response_as_json(response: Response) -> Dict[Any, Any]:
    """
    Checks whether `result` is a valid API response.
    A result is considered invalid if:
        - The server returned an HTTP response code other than 200
    """
    try:
        result_json = cast(Dict[Any, Any], orjson.loads(response.body))
    except ValueError:
        result_json = {}

    if response.status_code == HTTPStatus.OK:
        return result_json

    raise QiwiAPIError(response)


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
