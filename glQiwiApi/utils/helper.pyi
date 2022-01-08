from __future__ import annotations

import logging
from typing import Any, Dict, Union, TypeVar, Callable

import glQiwiApi.core.synchronous.adapter

N = TypeVar("N", bound=Callable[..., Any])

class measure_time(object):  # NOQA
    _logger: Union[logging.Logger, None] = None

    def __init__(self, logger: Union[logging.Logger, None] = None) -> None: ...

    def __call__(self, func: N) -> N: ...

    def _log(self, msg: str, *args: Any) -> None: ...


class allow_response_code:  # NOQA
    status_code: int

    def __init__(self, status_code: int) -> None: ...

    def __call__(
            self, func: glQiwiApi.core.synchronous.adapter.N
    ) -> glQiwiApi.core.synchronous.adapter.N: ...


class override_error_message:  # NOQA
    status_codes: Dict[int, Dict[str, str]]

    def __init__(self, status_codes: Dict[int, Dict[str, str]]): ...

    def __call__(
            self, func: glQiwiApi.core.synchronous.adapter.N
    ) -> glQiwiApi.core.synchronous.adapter.N: ...
