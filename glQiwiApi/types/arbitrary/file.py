from __future__ import annotations

import asyncio
import inspect
import pathlib
from typing import Any, BinaryIO, Union

from glQiwiApi.types.arbitrary.inputs import AbstractInput
from glQiwiApi.utils.compat import aiofiles

CHUNK_SIZE = 65536

StrOrBytesPath = Union[str, bytes, pathlib.Path]  # stable

_OpenFile = Union[StrOrBytesPath, int]


class File:
    def __init__(self, input: AbstractInput[Any]) -> None:
        self._input = input

    def get_filename(self) -> str:
        return self._input.get_filename()

    def get_underlying_file_descriptor(self) -> BinaryIO:
        return self._input.get_file()

    def get_path(self) -> str:
        return self._input.get_path()

    def save(self, path: StrOrBytesPath, chunk_size: int = CHUNK_SIZE) -> None:
        file_descriptor = self.get_underlying_file_descriptor()
        with open(path, 'wb') as fp:
            while True:
                data = file_descriptor.read(chunk_size)
                if not data:
                    break
                fp.write(data)
            fp.flush()

        if file_descriptor.seekable():
            file_descriptor.seek(0)

    async def save_asynchronously(
        self, path: StrOrBytesPath, chunk_size: int = CHUNK_SIZE
    ) -> None:
        file_descriptor = self.get_underlying_file_descriptor()
        async with aiofiles.open(path, 'wb') as fp:
            while True:
                data = file_descriptor.read(chunk_size)
                if not data:
                    break
                await fp.write(data)
            await fp.flush()

        if file_descriptor.seekable():
            file_descriptor.seek(0)

    def __str__(self) -> str:
        try:
            return self.get_filename()
        except TypeError:
            return '<File(binary stream underlies)>'

    def __del__(self) -> None:
        if not hasattr(self, '_input'):
            return

        if inspect.iscoroutinefunction(self._input.close()):  # type: ignore  # noqa
            return asyncio.ensure_future(self._input.close())  # type: ignore # noqa
        self._input.close()

    __repr__ = __str__
