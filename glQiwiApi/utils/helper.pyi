from __future__ import annotations

import logging
from typing import Any, Callable, Collection, Dict, Union

import glQiwiApi.core.synchronous.adapter
from glQiwiApi import QiwiWrapper, types

class measure_time(object):  # NOQA
    _logger: Union[logging.Logger, None] = None
    def __init__(self, logger: Union[logging.Logger, None] = None) -> None: ...
    def __call__(
        self, func: glQiwiApi.core.synchronous.adapter.N
    ) -> glQiwiApi.core.synchronous.adapter.N: ...
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

class require:  # NOQA
    _required_attrs: Collection[str]
    def __init__(self, *params: str): ...
    def __call__(
        self, func: glQiwiApi.core.synchronous.adapter.N
    ) -> glQiwiApi.core.synchronous.adapter.N: ...
    def check_is_object_contains_required_attrs(
        self, c: QiwiWrapper, func: Callable[..., Any]
    ) -> None: ...
