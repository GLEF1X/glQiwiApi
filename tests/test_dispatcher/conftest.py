import asyncio
import functools
from typing import Optional, Tuple

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient
from aiohttp.test_utils import TestServer, BaseTestServer

from glQiwiApi.core.web_hooks import server
from glQiwiApi.core.web_hooks.dispatcher import Dispatcher
from glQiwiApi.core.web_hooks.server import _check_ip  # NOQA
from glQiwiApi.core.web_hooks.server import _check_ip  # NOQA
from glQiwiApi.core.web_hooks.server import _check_ip  # NOQA
from glQiwiApi.types import Notification, WebHook
from tests.types.dataset import NOTIFICATION_RAW_DATA, WEBHOOK_RAW_DATA

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(name="test_aiohttp")
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


@pytest.fixture(name="bill_event", scope="module")
def bill_event_fixture():
    yield asyncio.Event()


@pytest.fixture(name="txn_event", scope="module")
def transaction_event_fixture():
    yield asyncio.Event()


@pytest.fixture(name="dp", scope="module")
async def dp_fixture():
    dp = Dispatcher()
    yield dp


@pytest.fixture(name="add_handlers", scope="module")
def add_handlers(dp: Dispatcher, txn_event: asyncio.Event, bill_event: asyncio.Event):
    dp.register_bill_handler(functools.partial(my_bill_handler, event=bill_event))
    dp.register_transaction_handler(
        functools.partial(my_transaction_handler, event=txn_event)
    )
    return txn_event, bill_event


@pytest.fixture(name="app", scope="module")
async def app_fixture(
    dp: Dispatcher, add_handlers: Tuple[asyncio.Event, asyncio.Event]
):
    txn_event, bill_event = add_handlers
    app = web.Application()
    app["bill_event"] = bill_event
    app["txn_event"] = txn_event
    return server.setup(dp, app=app)
