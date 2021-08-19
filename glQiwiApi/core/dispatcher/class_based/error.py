from __future__ import annotations

import abc
from typing import Any

from .base import Handler


class ErrorHandler(Handler[Exception], abc.ABC):
    def __init__(self, event: Exception, *args: Any) -> None:
        super().__init__(event)
        self.args = args

    @property
    def exception_name(self) -> str:
        return self.event.__class__.__qualname__
