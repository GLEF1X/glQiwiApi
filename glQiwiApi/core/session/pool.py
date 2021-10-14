from __future__ import annotations

import abc
import asyncio
from types import TracebackType
from typing import Any, Generic, Optional, Protocol, Type, TypeVar, cast, runtime_checkable, List

import aiohttp

_SessionType = TypeVar("_SessionType", bound=Any)
_SessionHolderType = TypeVar("_SessionHolderType", bound="AbstractSessionPool[Any]")


@runtime_checkable
class Closable(Protocol):
    async def close(self) -> None:
        ...


class AbstractSessionPool(abc.ABC, Generic[_SessionType]):
    """
    Manages the lifecycle of the session (s) and allows spoofing
    library for requests, for example from aiohttp to httpx without any problem.
    Holder is lazy and allocates in his own state session on first call, not on instantiation.
    """

    def __init__(self, **kwargs: Any) -> None:
        self._session_pool: List[_SessionType] = []
        self._session_kwargs = kwargs
        self._last_working_session: Optional[_SessionType] = None

    async def close_all(self) -> None:
        raise NotImplementedError

    async def get(self) -> _SessionType:
        if self._has_prepared_sessions_in_pool():
            await self._cleanup_rotten_sessions()
            return self._session_pool.pop(-1)
        return await self._instantiate_new_session()

    def put(self, session: _SessionType):
        self._session_pool.append(session)

    def acquire(self) -> AbstractSessionPool[_SessionType]:
        return self

    @abc.abstractmethod
    def _has_prepared_sessions_in_pool(self) -> bool:
        pass

    async def _cleanup_rotten_sessions(self) -> None:
        pass

    @abc.abstractmethod
    async def _instantiate_new_session(self) -> _SessionType:
        pass

    def update_session_kwargs(self, **kwargs: Any) -> None:
        self._session_kwargs.update(kwargs)

    async def __aenter__(self: _SessionHolderType) -> _SessionType:
        self._last_working_session = await self.get()
        return self._last_working_session

    async def __aexit__(
            self: _SessionHolderType,
            exc_type: Optional[Type[BaseException]],
            exc_value: Optional[BaseException],
            traceback: Optional[TracebackType],
    ) -> None:
        self.put(self._last_working_session)


class AiohttpSessionPool(AbstractSessionPool[aiohttp.ClientSession]):

    async def close_all(self) -> None:
        tasks = [
            asyncio.create_task(session.close())
            for session in self._session_pool
        ]
        await asyncio.gather(*tasks)

    def _has_prepared_sessions_in_pool(self) -> bool:
        for session in self._session_pool:
            if session.closed is False:
                return True
        return False

    async def _cleanup_rotten_sessions(self) -> None:
        for session in self._session_pool:
            if not session.closed:
                continue
            await session.close()
            del session

    async def _instantiate_new_session(self) -> _SessionType:
        session = cast(
            _SessionType,
            aiohttp.ClientSession(**self._session_kwargs)
        )
        self.put(session)
        return session
