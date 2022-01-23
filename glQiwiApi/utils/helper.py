from __future__ import annotations

import functools as ft


class allow_response_code:  # NOQA
    def __init__(self, status_code) -> None:
        self.status_code = status_code

    def __call__(self, func):
        status_code = self.status_code

        @ft.wraps(func)
        async def wrapper(*args, **kwargs):
            from glQiwiApi.qiwi.exceptions import APIError

            try:
                await func(*args, **kwargs)
            except APIError as error:
                if error.status_code == str(status_code):
                    info = error.request_data
                    return {"success": True} if not info else info
                return {"success": False}

        return wrapper


class override_error_message:  # NOQA
    def __init__(self, status_codes) -> None:
        self.status_codes = status_codes

    def __call__(self, func):
        status_codes = self.status_codes

        @ft.wraps(func)
        async def wrapper(*args, **kwargs):
            from glQiwiApi.qiwi.exceptions import APIError

            try:
                return await func(*args, **kwargs)
            except APIError as ex:
                if int(ex.status_code) in status_codes.keys():
                    error = status_codes.get(int(ex.status_code))
                    ex = APIError(
                        message=error.get("message"),
                        status_code=ex.status_code,
                        request_data=error.get("json_info"),
                        additional_info=ex.additional_info,
                    )
                raise ex from None

        return wrapper
