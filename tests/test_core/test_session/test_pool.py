from typing import AsyncGenerator

import aiohttp
import pytest

from glQiwiApi.core.session.pool import AiohttpSessionPool, StateError

pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def session_pool() -> AsyncGenerator[AiohttpSessionPool, None]:
    pool = AiohttpSessionPool()
    yield pool
    await pool.close()


@pytest.fixture()
async def initialized_pool(
        session_pool: AiohttpSessionPool) -> AsyncGenerator[AiohttpSessionPool, None]:
    await session_pool._initialize()
    yield session_pool
    await session_pool.close()


async def test_acquire(initialized_pool: AiohttpSessionPool):
    async with initialized_pool.acquire() as new_session:
        assert isinstance(new_session, aiohttp.ClientSession) is True
    assert initialized_pool.is_empty() is False


async def test_async_context(session_pool: AiohttpSessionPool):
    async with session_pool as pool:
        assert pool.is_empty() is False


async def test_initialize(initialized_pool: AiohttpSessionPool):
    assert initialized_pool.is_empty() is False


async def test_close_all(initialized_pool: AiohttpSessionPool):
    await initialized_pool.close()
    assert initialized_pool.is_empty() is True


async def test_get(initialized_pool: AiohttpSessionPool):
    session = await initialized_pool.get()
    assert isinstance(session, aiohttp.ClientSession) is True
    assert initialized_pool.is_empty() is True


async def test_get_new_session(session_pool: AiohttpSessionPool):
    session: aiohttp.ClientSession = await session_pool.get_new_session()
    assert isinstance(session, aiohttp.ClientSession) is True
    assert session_pool.is_empty() is True


async def test_put(session_pool: AiohttpSessionPool):
    session: aiohttp.ClientSession = await session_pool.get_new_session()
    await session_pool.put(session)
    assert await session_pool.get() == session


async def test_close_session(initialized_pool: AiohttpSessionPool):
    async with initialized_pool.acquire() as session:
        await initialized_pool.close_session(session)
        assert session.closed is True


async def test_failure_if_pool_is_not_initialized(session_pool: AiohttpSessionPool):
    with pytest.raises(StateError):
        async with session_pool.acquire() as _:
            ...
