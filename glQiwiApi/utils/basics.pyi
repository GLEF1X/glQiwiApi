from datetime import datetime
from typing import Any, Union, Optional, Dict, Type, List, Literal, MutableMapping, Tuple

from glQiwiApi import types


def measure_time(func: types.F) -> None: ...


def datetime_to_str_in_iso(obj: datetime, yoo_money_format: bool = False) -> str: ...


def format_objects_for_fill(data: dict, transfers: Dict[str, str]) -> dict: ...


def parse_auth_link(response_data: Union[str, bytes]) -> Optional[str]: ...


def parse_headers(content_json: bool = False, auth: bool = False) -> Dict[Any, Any]: ...


def format_objects(iterable_obj: Union[list, tuple], obj: Type,
                   transfers: Optional[Dict[str, str]] = None) -> Optional[List[types.BasicTypes]]: ...


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
        pay_source_filter: Optional[Literal['qw', 'card', 'mobile']] = None
) -> Dict[MutableMapping, Any]: ...


def multiply_objects_parse(
        lst_of_objects: Union[List[str], Tuple[str, ...]], model: Type[types.PydanticTypes]
) -> List[types.PydanticTypes]: ...


def dump_response(func: types.F) -> types.F: ...


def simple_multiply_parse(lst_of_objects: Union[List[Union[dict, str]], dict],
                          model: Type[types.PydanticTypes]) -> List[types.PydanticTypes]: ...


def custom_load(data: Dict[Any, Any]) -> Dict[str, Any]: ...


def allow_response_code(status_code: Union[str, int]) -> types.F: ...