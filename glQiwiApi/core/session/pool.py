from __future__ import annotations

import abc
import asyncio
import logging
from types import TracebackType
from typing import Any, Generic, Optional, Type, TypeVar, cast, Generator

import aiohttp

_SessionType = TypeVar("_SessionType", bound=Any)
_SessionPoolType = TypeVar("_SessionPoolType", bound="SessionPool[Any]")

logger = logging.getLogger(__name__)

DEFAULT_MAXSIZE = 50
DEFAULT_PREPARED_SESSIONS = 1


class StateError(Exception):
    pass


class PoolAcquireContext(Generic[_SessionType]):

    def __init__(self, pool: SessionPool[_SessionType]):
        self._pool = pool
        self._session: Optional[_SessionType] = None

    async def __aenter__(self) -> _SessionType:
        self._session = await self._pool.get()
        return self._session

    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_value: Optional[BaseException],
            traceback: Optional[TracebackType],
    ) -> None:
        await self._pool.put(cast(_SessionType, self._session))


class SessionPool(abc.ABC, Generic[_SessionType]):
    """
    Manages the lifecycle of pool of the session (s) and allows spoofing
    library for requests, for example from aiohttp to httpx without any problem.
    Holder is lazy and allocates in his own state session on first call, not on instantiation.
    """

    def __init__(self, prepared_sessions: int = DEFAULT_PREPARED_SESSIONS,
                 maxsize: int = DEFAULT_MAXSIZE, **kwargs: Any) -> None:
        if prepared_sessions > maxsize:
            raise TypeError("Prepared sessions can't be greater than maxsize")
        self._session_queue: asyncio.Queue[_SessionType] = asyncio.Queue(maxsize=maxsize)
        self._session_kwargs = kwargs
        self._prepared_sessions = prepared_sessions
        self._initialized = False
        self._maxsize = maxsize

    async def get(self) -> _SessionType:
        return self._session_queue.get_nowait()

    async def put(self, session: _SessionType) -> None:
        await self._session_queue.put(session)

    @abc.abstractmethod
    async def close_session(self, session: _SessionType) -> None:
        pass

    async def _initialize(self) -> SessionPool[_SessionType]:
        if self._initialized is True:
            return self
        tasks = []
        for _ in range(0, self._prepared_sessions):
            async def prepare_session():
                self._session_queue.put_nowait(await self.get_new_session())

            tasks.append(asyncio.create_task(prepare_session()))

        await asyncio.gather(*tasks)
        self._initialized = True
        return self

    @abc.abstractmethod
    async def get_new_session(self) -> _SessionType:
        pass

    def acquire(self) -> PoolAcquireContext[_SessionType]:
        if not self._initialized:
            raise StateError("Can't acquire uninitialized pool.")
        return PoolAcquireContext(self)

    def is_empty(self) -> bool:
        return self._session_queue.empty()

    def update_session_kwargs(self, **kwargs: Any) -> None:
        self._session_kwargs.update(kwargs)

    async def close(self) -> None:
        warning_callback = asyncio.get_event_loop().call_later(60, self._warn_on_long_close)
        try:
            await self._close()
        finally:
            if warning_callback is not None:
                warning_callback.cancel()
            self._initialized = False

    @abc.abstractmethod
    async def _close(self) -> None:
        pass

    def _warn_on_long_close(self) -> None:
        logger.warning('SessionPool.close() is taking over 60 seconds to complete. '
                       'Check if you have any unreleased connections left. '
                       'Use asyncio.wait_for() to set a timeout for '
                       'SessionPool.close().')

    async def __aenter__(self) -> SessionPool[_SessionType]:
        await self._initialize()
        return self

    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_value: Optional[BaseException],
            traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    def __await__(self) -> Generator[Any, Any, Any]:
        if self._initialized is True:
            async def empty(): pass

            return empty().__await__()
        return self._initialize().__await__()


class LifoSessionPool(SessionPool[_SessionType], abc.ABC):

    def __init__(self, **kwargs: Any) -> None:
        SessionPool.__init__(self, **kwargs)
        self._session_queue: asyncio.LifoQueue[_SessionType] = asyncio.LifoQueue()


class AiohttpSessionPool(SessionPool[aiohttp.ClientSession]):

    async def _close(self) -> None:
        try:
            session = self._session_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
        else:
            await asyncio.gather(session.close(), self.close())

    async def get_new_session(self) -> _SessionType:
        session = cast(
            _SessionType,
            aiohttp.ClientSession(**self._session_kwargs)
        )
        return session

    async def close_session(self, session: _SessionType) -> None:
        await session.close()
