import asyncio
import functools
from typing import Awaitable, Callable, Optional

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer, BaseTestServer
from pytest_mock import MockerFixture

from glQiwiApi.core.web_hooks import server
from glQiwiApi.core.web_hooks.config import (
    DEFAULT_QIWI_BILLS_WEBHOOK_PATH,
    DEFAULT_QIWI_WEBHOOK_PATH,
)
from glQiwiApi.core.web_hooks.dispatcher import Dispatcher
from glQiwiApi.core.web_hooks.server import _check_ip  # NOQA
from glQiwiApi.types import Notification, WebHook
from tests.types.dataset import NOTIFICATION_RAW_DATA, WEBHOOK_RAW_DATA

pytestmark = pytest.mark.asyncio


async def my_bill_handler(update: Notification, event: Optional[asyncio.Event] = None):
    if not isinstance(event, asyncio.Event):
        raise TypeError()
    assert update == Notification.parse_raw(NOTIFICATION_RAW_DATA)
    event.set()


async def my_transaction_handler(
    update: WebHook, event: Optional[asyncio.Event] = None
):
    if not isinstance(event, asyncio.Event):
        raise TypeError()
    assert update == WebHook.parse_raw(WEBHOOK_RAW_DATA)
    event.set()


@pytest.fixture()
async def aiohttp_client():
    """Factory to create a TestClient instance.

    aiohttp_client(app, **kwargs)
    aiohttp_client(server, **kwargs)
    aiohttp_client(raw_server, **kwargs)
    """
    clients = []

    async def go(__param, *, server_kwargs=None, **kwargs):  # type: ignore
        if isinstance(__param, web.Application):
            server_kwargs = server_kwargs or {}
            server = TestServer(__param, **server_kwargs)
            client = TestClient(server, **kwargs)
        elif isinstance(__param, BaseTestServer):
            client = TestClient(__param, **kwargs)
        else:
            raise ValueError("Unknown argument type: %r" % type(__param))

        await client.start_server()
        clients.append(client)
        return client

    yield go

    async def finalize():  # type: ignore
        while clients:
            await clients.pop().close()

    await finalize()


@pytest.fixture(name="app")
async def app_fixture():
    dp = Dispatcher()
    bill_event = asyncio.Event()
    txn_event = asyncio.Event()
    dp.register_bill_handler(functools.partial(my_bill_handler, event=bill_event))
    dp.register_transaction_handler(
        functools.partial(my_transaction_handler, event=txn_event)
    )
    app = web.Application()
    app["bill_event"] = bill_event
    app["txn_event"] = txn_event
    return server.setup(dp, app=app)


async def test_bill_webhooks(
    app: web.Application,
    aiohttp_client: Callable[..., Awaitable[TestClient]],
    mocker: MockerFixture,
):
    client = await aiohttp_client(app)
    bill_event: asyncio.Event = app["bill_event"]
    txn_event: asyncio.Event = app["txn_event"]
    # skip ip validation
    mocker.patch("glQiwiApi.core.web_hooks.server._check_ip", return_value=True)
    bill_response = await client.post(
        path=DEFAULT_QIWI_BILLS_WEBHOOK_PATH, json=NOTIFICATION_RAW_DATA
    )
    assert bill_response.status == 200
    assert bill_event.is_set()
    bill_event.clear()
    # skip hash validation
    mocker.patch(
        "glQiwiApi.core.web_hooks.server.QiwiWalletWebView._hash_validator",
        return_value=None,
    )
    transaction_response = await client.post(
        path=DEFAULT_QIWI_WEBHOOK_PATH, json=WEBHOOK_RAW_DATA
    )
    assert transaction_response.status == 200
    assert txn_event.is_set()


async def test_check_ip_address():
    assert _check_ip(ip_address="79.142.16.0")
    assert not _check_ip(ip_address="127.0.0.1")
