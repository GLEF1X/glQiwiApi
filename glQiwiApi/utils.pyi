from datetime import datetime
from typing import Any, Union, Optional, Dict, Type, List, Literal, MutableMapping

from glQiwiApi import data as basic_types, types


def measure_time(func: types.F) -> None: ...


def datetime_to_str_in_iso(obj: datetime, yoo_money_format: bool = False) -> str: ...


def parse_auth_link(response_data: Union[str, bytes]) -> Optional[str]: ...


def parse_headers(content_json: bool = False, auth: bool = False) -> Dict[Any, Any]: ...


class DataFormatter:
    def format_objects(self, iterable_obj: Union[list, tuple], obj: Type[types.BasicTypes],
                       transfers: Optional[Dict[str, str]] = None) -> Optional[List[types.BasicTypes]]: ...

    def set_data_to_wallet(self, data: basic_types.WrapperData,
                           to_number: str,
                           trans_sum: Union[str, int, float],
                           comment: str,
                           currency: str = '643') -> types.WrapperData: ...

    def set_data_p2p_create(
            self, wrapped_data: basic_types.WrapperData,
            amount: Union[str, int, float],
            life_time: str,
            comment: Optional[str] = None,
            theme_code: Optional[str] = None,
            pay_source_filter: Optional[Literal['qw', 'card', 'mobile']] = None
    ) -> Dict[MutableMapping, Any]: ...
