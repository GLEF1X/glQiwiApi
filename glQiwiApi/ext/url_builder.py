from __future__ import annotations

import re
import types
from collections import namedtuple
from typing import TypeVar, Type, Optional, Any, Callable

from glQiwiApi.core.web_hooks.config import DEFAULT_QIWI_BILLS_WEBHOOK_PATH

_URL = TypeVar("_URL", bound="WebhookURL")


class WebhookURL(
    namedtuple(
        "WebhookURL",
        ["host", "webhook_path", "port"],
    )
):
    host: str
    webhook_path: Optional[str]
    port: int

    @classmethod
    def create(
        cls: Type[_URL], host: str, port: int, webhook_path: Optional[str] = None
    ) -> _URL:
        return cls(
            host=cls._assert_host(host, param_name="host"),
            webhook_path=cls._assert_str(
                webhook_path,
                param_name="webhook_path",
                additional_filter=lambda v: v.startswith("/"),
            ),
            port=cls._assert_int(port, param_name="port"),
        )

    @classmethod
    def _assert_int(cls, v: Optional[Any], *, param_name: str) -> Optional[int]:
        if v is None:
            return v

        if not isinstance(v, int):
            raise TypeError("%s must be integer" % param_name)
        return v

    @classmethod
    def _assert_str(
        cls,
        v: Optional[Any],
        *,
        param_name: str,
        additional_filter: Optional[Callable[[Any], bool]] = None,
    ) -> Optional[str]:
        if v is None:
            return v

        if not isinstance(v, str):
            raise TypeError("%s must be a string" % param_name)
        if isinstance(additional_filter, types.LambdaType):
            if not additional_filter(v):
                raise TypeError(
                    f"%s must pass a custom filter {additional_filter}" % param_name
                )
        return v

    @classmethod
    def _assert_host(cls, v: Any, *, param_name: str) -> str:
        regex_pattern = re.compile(
            r"^(http(s?)://)?"
            r"(((www\.)?[a-zA-Z0-9.\-_]+"
            r"(\.[a-zA-Z]{2,6})+)|"
            r"(\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.)"
            r"{3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b))"
            r"(/[a-zA-Z0-9_\-\s./?%#&=]*)?$"
        )
        if not re.match(regex_pattern, v):
            raise TypeError(
                "%s must be like https://127.0.0.1/ or https://website.com/"
                % param_name
            )
        return v

    def render_as_string(self) -> str:
        host = self.host
        webhook_path = self.webhook_path
        port = self.port

        if self.host.endswith("/"):
            host = host[: host.rindex("/")]
        if webhook_path is None:
            webhook_path = DEFAULT_QIWI_BILLS_WEBHOOK_PATH

        return f"{host}:{port}{webhook_path}"
