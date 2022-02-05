import functools as ft
from typing import TypeVar, Callable, Any, cast

T = TypeVar("T", bound=Callable[..., Any])


class allow_response_code:  # NOQA
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code

    def __call__(self, func: T) -> T:
        @ft.wraps(func)
        async def wrapper(*args, **kwargs):
            from glQiwiApi.qiwi.exceptions import QiwiAPIError

            try:
                await func(*args, **kwargs)
            except QiwiAPIError as error:
                if error.http_response.status_code != self.status_code:
                    raise error

        return cast(T, wrapper)
