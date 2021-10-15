from __future__ import annotations

import abc
import asyncio
from types import TracebackType
from typing import Any, Generic, Optional, Protocol, Type, TypeVar, cast, runtime_checkable

import aiohttp

_SessionType = TypeVar("_SessionType", bound=Any)
_SessionHolderType = TypeVar("_SessionHolderType", bound="AbstractSessionPool[Any]")


@runtime_checkable
class Closable(Protocol):
    async def close(self) -> None:
        ...


class AbstractSessionPool(abc.ABC, Generic[_SessionType]):
    """
    Manages the lifecycle of pool of the session (s) and allows spoofing
    library for requests, for example from aiohttp to httpx without any problem.
    Holder is lazy and allocates in his own state session on first call, not on instantiation.
    """

    def __init__(self, **kwargs: Any) -> None:
        self._session_queue: asyncio.Queue[_SessionType] = asyncio.Queue()
        self._session_kwargs = kwargs
        self._working_session: Optional[_SessionType] = None

    async def close_all(self) -> None:
        raise NotImplementedError

    async def get(self) -> _SessionType:
        return self._session_queue.get_nowait()

    async def put(self, session: _SessionType) -> None:
        await self._session_queue.put(session)

    async def warm_up(self) -> None:
        self._working_session = await self.get_new_session()
        await self.put(self._working_session)

    def acquire(self) -> AbstractSessionPool[_SessionType]:
        return self

    def is_empty(self) -> bool:
        return self._session_queue.empty()

    def update_session_kwargs(self, **kwargs: Any) -> None:
        self._session_kwargs.update(kwargs)

    async def __aenter__(self: _SessionHolderType) -> _SessionType:
        try:
            self._working_session = await self.get()
        except asyncio.QueueEmpty:
            self._working_session = await self.get_new_session()
        return cast(_SessionType, self._working_session)

    async def __aexit__(
            self: _SessionHolderType,
            exc_type: Optional[Type[BaseException]],
            exc_value: Optional[BaseException],
            traceback: Optional[TracebackType],
    ) -> None:
        if self._working_session is not None:
            await self.put(self._working_session)

    def __del__(self) -> None:
        if self._session_queue.empty() is False:
            del self._session_queue
        if self._working_session is not None:
            del self._working_session

    async def _cleanup_rotten_sessions(self) -> None:
        pass

    @abc.abstractmethod
    async def get_new_session(self) -> _SessionType:
        pass


class AiohttpSessionPool(AbstractSessionPool[aiohttp.ClientSession]):

    async def close_all(self) -> None:
        try:
            session = self._session_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
        else:
            await asyncio.gather(session.close(), self.close_all())

    async def get_new_session(self) -> _SessionType:
        session = cast(
            _SessionType,
            aiohttp.ClientSession(**self._session_kwargs)
        )
        return session
