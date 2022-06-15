import re
from typing import Any, Dict, TypeVar, cast

from pydantic import BaseModel

Model = TypeVar('Model', bound=BaseModel)
DEFAULT_EXCLUDE = ('cls', 'self', '__class__')


def filter_dictionary_none_values(dictionary: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Pop NoneType values and convert everything to str, designed?for=params
    :param dictionary: source dict
    :return: filtered dict
    """
    return {k: str(v) for k, v in dictionary.items() if v is not None}


def make_payload(**kwargs: Any) -> Dict[Any, Any]:
    exclude_list = kwargs.pop('exclude', ())
    return {
        key: value
        for key, value in kwargs.items()
        if key not in DEFAULT_EXCLUDE + exclude_list and value is not None
    }


def parse_auth_link(response_data: str) -> str:
    """
    Parse link for getting code, which needs to be entered in the method
    get_access_token
    :param response_data:
    """
    regexp = re.compile(
        r'https://yoomoney.ru/oauth2/authorize[?]requestid[=]\w+'
    )  # pragma: no cover
    return cast(str, re.findall(regexp, str(response_data))[0])  # pragma: no cover
