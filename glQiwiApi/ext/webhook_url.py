from __future__ import annotations

import re
from collections import namedtuple
from typing import Any, Optional, Pattern, Type, TypeVar, cast

from glQiwiApi.core.event_fetching.webhooks.config import DEFAULT_QIWI_WEBHOOK_PATH

_URL = TypeVar("_URL", bound="WebhookURL")

# Url without port e.g. https://127.0.0.1/ or https://website.com/
HOST_REGEX: Pattern[str] = re.compile(
    r"^(http(s?)://)?"
    r"(((www\.)?[a-zA-Z0-9.\-_]+"
    r"(\.[a-zA-Z]{2,6})+)|"
    r"(\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.)"
    r"{3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b))"
    r"(/[a-zA-Z0-9_\-\s./?%#&=]*)?$"
)


class WebhookURL(
    namedtuple(
        "WebhookURL",
        ["host", "webhook_path", "port", "https"],
    )
):
    host: str
    webhook_path: Optional[str]
    port: Optional[int]
    https: bool = False

    @classmethod
    def create(
        cls: Type[_URL],
        host: str,
        port: Optional[int] = None,
        webhook_path: Optional[str] = None,
        https: bool = False,
    ) -> _URL:
        return cls(
            host=cls._assert_host(host, param_name="host"),
            webhook_path=cls._assert_str(webhook_path, param_name="webhook_path"),
            port=cls._assert_int(port, param_name="port"),
            https=https,
        )

    @classmethod
    def _assert_int(cls, v: Optional[Any], *, param_name: str) -> Optional[int]:
        if v is None:
            return v

        if not isinstance(v, int):
            raise TypeError("%s must be integer" % param_name)
        return v

    @classmethod
    def _assert_str(cls, v: Optional[Any], *, param_name: str) -> Optional[str]:
        if v is None:
            return v

        if not isinstance(v, str):
            raise TypeError("%s must be a string" % param_name)
        return v

    @classmethod
    def _assert_host(cls, v: Any, *, param_name: str) -> str:
        if not re.match(HOST_REGEX, v):
            raise TypeError(
                "%s must be like https://127.0.0.1/ or https://website.com/" % param_name
            )
        return cast(str, v)

    def render(self) -> str:
        host = self.host
        if self.webhook_path is None:
            # Here we use `DEFAULT_QIWI_WEBHOOK_PATH` instead of DEFAULT_QIWI_BILLS_WEBHOOK_PATH
            # because the second you need to register directly in QIWI P2P API and it's no need to build endpoint to it
            self.webhook_path = DEFAULT_QIWI_WEBHOOK_PATH
        if self.port is not None:
            host += f":{self.port}"
        if self._doesnt_contains_slash():
            host += "/"
        if self.https:
            scheme = "https://"
        else:
            scheme = "http://"
        return f"{scheme}{host}{self.webhook_path}"

    def _doesnt_contains_slash(self) -> bool:
        return not (self.host.endswith("/") and self.webhook_path.startswith("/"))  # type: ignore
