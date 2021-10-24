from __future__ import annotations

from types import TracebackType
from typing import Any, AsyncContextManager, NoReturn, Optional, Type


class ModuleNotInstalledException(Exception):
    pass


class CompatAsyncContextManager:

    def __init__(self, not_installed_module_name: str) -> None:
        self._not_installed_module_name = not_installed_module_name

    async def __aenter__(self) -> NoReturn:
        raise ModuleNotInstalledException(
            f"Module {self._not_installed_module_name} not installed and you can't use it's "
            f"functionality till you install this module"
        )

    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_value: Optional[BaseException],
            traceback: Optional[TracebackType],
    ) -> None:
        raise ModuleNotInstalledException(
            f"Module {self._not_installed_module_name} not installed and you can't use it's "
            f"functionality till you install this module"
        )


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
