from __future__ import annotations

import asyncio
import concurrent.futures as futures
import functools as ft
from contextvars import ContextVar


class AdaptiveExecutor(futures.ThreadPoolExecutor):
    """object: AdaptiveExecutor"""

    def __init__(self, max_workers=None, **kwargs):
        super().__init__(max_workers, 'sync_adapter_', **kwargs)
        self.max_workers = max_workers
        self.is_from_running_loop = ContextVar('Adapter_', default=False)


def execute_async_as_sync(func, *args, **kwargs):
    """
    Function to execute async functions synchronously

    :param func: Async function, which you want to execute in synchronous code
    :param args: args, which need your async func
    :param kwargs: kwargs, which need your async func
    """
    try:
        shutdown_callback = kwargs.pop('__shutdown__callback__')
    except KeyError:
        shutdown_callback = None
    loop, executor = _construct_executor_and_loop()
    wrapped_future = asyncio.run_coroutine_threadsafe(func(*args, **kwargs), loop=loop)
    executor.submit(run_forever_safe, loop, shutdown_callback)
    try:
        # Get result
        return await_sync(wrapped_future)
    finally:
        # Cleanup
        _on_shutdown(executor, loop)


def _construct_executor_and_loop():
    """Get or create new event loop"""
    loop = take_event_loop()
    executor = AdaptiveExecutor()
    loop.set_default_executor(executor)
    return loop, executor


def take_event_loop(set_debug: bool = False):
    """
    Get new or running event loop

    :param set_debug:
    """
    try:
        loop = asyncio.get_running_loop()
        if loop.is_closed():
            raise RuntimeError()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.set_debug(set_debug)
    return loop


def run_forever_safe(loop, callback=None) -> None:
    """run a loop for ever and clean up after being stopped"""

    loop.run_forever()
    # NOTE: loop.run_forever returns after calling loop.stop

    safe_cancel(loop=loop, callback=callback)


def safe_cancel(loop, callback) -> None:
    """cancel all tasks and close the loop gracefully"""

    loop_tasks_all = asyncio.all_tasks(loop=loop)

    # execute shutdown callback to gracefully shutdown your components
    if callback is not None:
        loop.run_until_complete(callback())

    # NOTE: `cancel` does not guarantee that the task will be cancelled
    for task in loop_tasks_all:
        task.cancel()

    for task in loop_tasks_all:
        if not (task.done() or task.cancelled()):
            try:
                # wait for task cancellations
                loop.run_until_complete(task)
            except asyncio.CancelledError:
                pass
    # Finally, close event loop
    loop.close()


def _cancel_future(loop, future, executor) -> None:
    """cancels future if any exception occurred"""
    executor.submit(loop.call_soon_threadsafe, future.cancel)


def _stop_loop(loop) -> None:
    """stops an event loop"""
    loop.stop()


def await_sync(future):
    """synchronously waits for a task"""
    return future.result()


def _on_shutdown(executor, loop):
    """Do some cleanup"""
    if not executor.is_from_running_loop.get():
        loop.call_soon_threadsafe(_stop_loop, loop)
    executor.shutdown(wait=True)


class async_as_sync:  # NOQA
    def __init__(self, async_shutdown_callback=None, sync_shutdown_callback=None):
        self._sync_shutdown_callback = sync_shutdown_callback
        self._async_shutdown_callback = async_shutdown_callback

    def __call__(self, func):
        @ft.wraps(func)
        def wrapper(*args, **kwargs):
            result = execute_async_as_sync(
                func, *args, __shutdown__callback__=self._async_shutdown_callback, **kwargs
            )
            if self._sync_shutdown_callback is not None:
                return self.execute_sync_callback(result)
            return result

        return wrapper

    def execute_sync_callback(self, result):
        return self._sync_shutdown_callback(result)
