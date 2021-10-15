from typing import AsyncGenerator

import aiohttp
import pytest

from glQiwiApi.core.session.pool import AiohttpSessionPool

pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def session_pool() -> AsyncGenerator[AiohttpSessionPool, None]:
    pool = AiohttpSessionPool()
    yield pool
    await pool.close_all()


class TestAiohttpSessionPool:

    async def test_as_context_manager(self, session_pool: AiohttpSessionPool):
        async with session_pool as new_session:
            assert isinstance(new_session, aiohttp.ClientSession) is True
        assert session_pool.is_empty() is False

    async def test_warm_up(self, session_pool: AiohttpSessionPool):
        await session_pool.warm_up()
        assert session_pool.is_empty() is False

    async def test_close_all(self, session_pool: AiohttpSessionPool):
        await session_pool.warm_up()
        await session_pool.close_all()
        assert session_pool.is_empty() is True

    async def test_acquire(self, session_pool: AiohttpSessionPool):
        async with session_pool.acquire() as new_session:
            assert isinstance(new_session, aiohttp.ClientSession) is True
        assert session_pool.is_empty() is False

    async def test_get(self, session_pool: AiohttpSessionPool):
        await session_pool.warm_up()
        session = await session_pool.get()
        assert isinstance(session, aiohttp.ClientSession) is True
        assert session_pool.is_empty() is True

    async def test_get_new_session(self, session_pool: AiohttpSessionPool):
        session: aiohttp.ClientSession = await session_pool.get_new_session()
        assert isinstance(session, aiohttp.ClientSession) is True
        assert session_pool.is_empty() is True

    async def test_put(self, session_pool: AiohttpSessionPool):
        session: aiohttp.ClientSession = await session_pool.get_new_session()
        await session_pool.put(session)
        assert await session_pool.get() == session
