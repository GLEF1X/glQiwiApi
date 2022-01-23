from __future__ import annotations

import logging
from typing import Any, Dict, Union, TypeVar, Callable

import glQiwiApi.core.synchronous.adapter

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
