from __future__ import annotations

import abc
from types import TracebackType
from typing import Any, Generic, Optional, Type, TypeVar, cast

import aiohttp

_SessionType = TypeVar("_SessionType", bound=Any)
_SessionHolderType = TypeVar("_SessionHolderType", bound="AbstractSessionHolder[Any]")


class AbstractSessionHolder(abc.ABC, Generic[_SessionType]):
    """
    Manages the lifecycle of the session (s) and allows spoofing
    library for requests, for example from aiohttp to httpx without any problem.
    Holder is lazy and allocates in his own state
    session on first call, not on instantiation.
    """

    def __init__(self, **kwargs: Any) -> None:
        self._session: Optional[_SessionType] = None
        self._session_kwargs = kwargs

    async def close(self) -> None:
        raise NotImplementedError

    async def get_session(self) -> _SessionType:
        raise NotImplementedError

    def update_session_kwargs(self, **kwargs: Any) -> None:
        self._session_kwargs.update(kwargs)

    async def __aenter__(self: AbstractSessionHolder[_SessionType]) -> _SessionType:
        self._session = await self.get_session()
        return self._session

    async def __aexit__(
            self: AbstractSessionHolder[_SessionType],
            exc_type: Optional[Type[BaseException]],
            exc_value: Optional[BaseException],
            traceback: Optional[TracebackType],
    ) -> None:
        await self.close()


class AiohttpSessionHolder(AbstractSessionHolder[aiohttp.ClientSession]):

    def __init__(self, **kwargs: Any):
        AbstractSessionHolder.__init__(self, **kwargs)

    async def close(self) -> None:
        if self._session_in_working_order():
            await self._session.close()

    async def get_session(self) -> _SessionType:
        if self._session_in_working_order():
            return self._session
        return await self._instantiate_new_session()

    def _session_in_working_order(self) -> bool:
        return self._session is not None and self._session.closed is False

    async def _instantiate_new_session(self) -> _SessionType:
        self._session: _SessionType = cast(
            _SessionType,
            aiohttp.ClientSession(**self._session_kwargs)
        )
        return self._session
