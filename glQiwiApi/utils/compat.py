from __future__ import annotations

import sys
from typing import Any, AsyncContextManager


class ModuleNotInstalledException(Exception):
    pass


class EmptyCls(object):
    def __init__(self) -> None:
        raise ModuleNotInstalledException()


try:
    import aiofiles
except ImportError:
    class aiofiles_compat:
        def open(self, *args: Any, **kwargs: Any) -> AsyncContextManager[Any]:
            raise ModuleNotInstalledException(
                "Module aiofiles not installed and you can't use it's "
                "functionality till you install this module."
            )
    aiofiles = aiofiles_compat()  # type: ignore

try:
    import orjson as json
except (ImportError, ModuleNotFoundError):
    import json  # type: ignore

try:
    from aiogram import Dispatcher
    from aiogram.types import InputFile
except (ModuleNotFoundError, ImportError):
    Dispatcher = EmptyCls
    InputFile = EmptyCls

if sys.version_info >= (3, 8):
    from typing import Literal as Literal
else:
    from typing_extensions import Literal
