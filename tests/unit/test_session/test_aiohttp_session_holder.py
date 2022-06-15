from typing import AsyncGenerator

import aiohttp
import pytest
from aiohttp import TCPConnector

from glQiwiApi.core.session.holder import AiohttpSessionHolder

pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def session_holder() -> AsyncGenerator[AiohttpSessionHolder, None]:
    holder = AiohttpSessionHolder()
    yield holder
    await holder.close()


async def test_get_session(session_holder: AiohttpSessionHolder) -> None:
    session: aiohttp.ClientSession = await session_holder.get_session()
    assert isinstance(session, aiohttp.ClientSession) is True


async def test_close(session_holder: AiohttpSessionHolder) -> None:
    await session_holder.get_session()
    await session_holder.close()
    assert session_holder._session.closed is True


async def test_update_session_kwargs(session_holder: AiohttpSessionHolder) -> None:
    conn = TCPConnector()
    session_holder.update_session_kwargs(connector=conn)
    assert session_holder._session_kwargs.get('connector') == conn


async def test_context_manager_of_holder(session_holder: AiohttpSessionHolder) -> None:
    async with session_holder as new_session:
        assert isinstance(new_session, aiohttp.ClientSession) is True
    assert new_session.closed is True
