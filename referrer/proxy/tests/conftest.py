from typing import Any, AsyncGenerator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient

from referrer.proxy.app import app

pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def initialized_app() -> AsyncGenerator[FastAPI, Any]:
    async with LifespanManager(app):
        yield app


@pytest.fixture()
async def client(initialized_app: FastAPI) -> AsyncGenerator[AsyncClient, Any]:
    async with AsyncClient(
        app=initialized_app,
        base_url="http://test",
        headers={"Content-Type": "application/json"},
    ) as client:  # type: AsyncClient
        yield client
