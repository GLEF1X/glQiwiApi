from __future__ import annotations

import asyncio
from concurrent.futures import Future
from typing import (
    Any,
    Optional,
    Coroutine,
    Callable,
    Awaitable,
)

from glQiwiApi import types

def run_forever_safe(
    loop: asyncio.AbstractEventLoop,
    callback: Optional[Callable[..., Awaitable[types.N]]] = None,
) -> None: ...
def safe_cancel(
    loop: asyncio.AbstractEventLoop,
    callback: Optional[Callable[..., Awaitable[types.N]]],
) -> None: ...
def _cancel_future(
    loop: asyncio.AbstractEventLoop,
    future: asyncio.Future[types.N],
    executor: types.AnyExecutor,
) -> None: ...
def _stop_loop(loop: asyncio.AbstractEventLoop) -> None: ...
def take_event_loop(set_debug: bool = False) -> asyncio.AbstractEventLoop: ...
def await_sync(future: Future[types.N]) -> types.N: ...
def execute_async_as_sync(
    func: Callable[..., Coroutine[Any, Any, types.N]], *args: object, **kwargs: object
) -> types.N: ...

class async_as_sync:  # NOQA
    _async_shutdown_callback: Optional[Callable[..., Awaitable[types.N]]]
    _sync_shutdown_callback: Optional[Callable[[Any], Any]]
    def __init__(
        self,
        async_shutdown_callback: Optional[Callable[..., Awaitable[types.N]]] = None,
        sync_shutdown_callback: Optional[Callable[[Any], Any]] = None,
    ) -> None: ...
    def __call__(
        self, func: Callable[..., Coroutine[Any, Any, types.N]]
    ) -> Callable[..., types.N]: ...
    def execute_sync_callback(self, result: Any) -> Any: ...
