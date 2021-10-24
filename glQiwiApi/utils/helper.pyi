from __future__ import annotations

import logging
from typing import Union, Any, Dict, Collection, Callable

from glQiwiApi import types, QiwiWrapper


class measure_time(object):  # NOQA
    _logger: Union[logging.Logger, None] = None

    def __init__(self, logger: Union[logging.Logger, None] = None) -> None: ...

    def __call__(self, func: types.N) -> types.N: ...

    def _log(self, msg: str, *args: Any) -> None: ...


class allow_response_code:  # NOQA
    status_code: int

    def __init__(self, status_code: int) -> None: ...

    def __call__(self, func: types.N) -> types.N: ...


class override_error_messages:  # NOQA
    status_codes: Dict[int, Dict[str, str]]

    def __init__(self, status_codes: Dict[int, Dict[str, str]]): ...

    def __call__(self, func: types.N) -> types.N: ...


class require:  # NOQA
    _required_attrs: Collection[str]

    def __init__(self, *params: str): ...

    def __call__(self, func: types.N) -> types.N: ...

    def check_is_object_contains_required_attrs(
            self,
            c: QiwiWrapper,
            func: Callable[..., Any]
    ) -> None:
        ...
