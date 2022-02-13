from __future__ import annotations

import asyncio
from concurrent import futures as futures
from concurrent.futures import Future
from typing import Any, Awaitable, Callable, Coroutine, Optional, TypeVar, Union

N = TypeVar("N")

def run_forever_safe(
    loop: asyncio.AbstractEventLoop,
    callback: Optional[Callable[..., Awaitable[N]]] = None,
) -> None: ...
def safe_cancel(
    loop: asyncio.AbstractEventLoop,
    callback: Optional[Callable[..., Awaitable[N]]],
) -> None: ...

AnyExecutor = Union[futures.ThreadPoolExecutor, futures.ProcessPoolExecutor, Optional[None]]

def _cancel_future(
    loop: asyncio.AbstractEventLoop,
    future: asyncio.Future[N],
    executor: AnyExecutor,
) -> None: ...
def _stop_loop(loop: asyncio.AbstractEventLoop) -> None: ...
def take_event_loop(set_debug: bool = False) -> asyncio.AbstractEventLoop: ...
def await_sync(future: Future[N]) -> N: ...
def execute_async_as_sync(
    func: Callable[..., Coroutine[Any, Any, N]], *args: object, **kwargs: object
) -> N: ...

class async_as_sync:  # NOQA
    _async_shutdown_callback: Optional[Callable[..., Awaitable[N]]]
    _sync_shutdown_callback: Optional[Callable[[Any], Any]]
    def __init__(
        self,
        async_shutdown_callback: Optional[Callable[..., Awaitable[N]]] = None,
        sync_shutdown_callback: Optional[Callable[[Any], Any]] = None,
    ) -> None: ...
    def __call__(self, func: Callable[..., Awaitable[N]]) -> Callable[..., N]: ...
    def execute_sync_callback(self, result: Any) -> Any: ...
