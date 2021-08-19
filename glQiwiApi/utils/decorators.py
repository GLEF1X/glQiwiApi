from __future__ import annotations

import functools as ft
import inspect
import time


class measure_time(object):  # NOQA
    def __init__(self, logger=None):
        self._logger = logger

    def __call__(self, func):
        if inspect.iscoroutinefunction(func) or inspect.iscoroutine(func):

            @ft.wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.monotonic()
                result = await func(*args, **kwargs)
                execute_time = time.monotonic() - start_time
                msg = "Function `%s` executed for %s secs"
                self._log(msg, func.__name__, execute_time)
                return result

        else:

            @ft.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.monotonic()
                result = func(*args, **kwargs)
                execute_time = time.monotonic() - start_time
                msg = "Function `%s` executed for %s secs"
                self._log(msg, func.__name__, execute_time)
                return result

        return wrapper

    def _log(self, msg, *args):
        if self._logger is not None:
            self._logger.info(msg, *args)
        else:
            print(msg % args)


class allow_response_code:  # NOQA
    def __init__(self, status_code) -> None:
        self.status_code = status_code

    def __call__(self, func):
        status_code = self.status_code

        @ft.wraps(func)
        async def wrapper(*args, **kwargs):
            from glQiwiApi import APIError

            try:
                await func(*args, **kwargs)
            except APIError as error:
                if error.status_code == str(status_code):
                    info = error.traceback_info
                    return {"success": True} if not info else info
                return {"success": False}

        return wrapper


class override_error_messages:  # NOQA
    def __init__(self, status_codes) -> None:
        self.status_codes = status_codes

    def __call__(self, func):
        status_codes = self.status_codes

        @ft.wraps(func)
        async def wrapper(*args, **kwargs):
            from glQiwiApi import APIError

            try:
                return await func(*args, **kwargs)
            except APIError as ex:
                if int(ex.status_code) in status_codes.keys():
                    error = status_codes.get(int(ex.status_code))
                    ex = APIError(
                        message=error.get("message"),
                        status_code=ex.status_code,
                        traceback_info=error.get("json_info"),
                        additional_info=ex.additional_info,
                    )
                raise ex from None

        return wrapper
