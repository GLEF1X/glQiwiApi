import asyncio
from typing import Awaitable, Callable

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient
from pytest_mock import MockerFixture

from glQiwiApi.core.web_hooks.config import (
    DEFAULT_QIWI_BILLS_WEBHOOK_PATH,
    DEFAULT_QIWI_WEBHOOK_PATH,
)
from glQiwiApi.core.web_hooks.server import _check_ip  # NOQA
from tests.types.dataset import NOTIFICATION_RAW_DATA, WEBHOOK_RAW_DATA

pytestmark = pytest.mark.asyncio


async def test_bill_webhooks(
        app: web.Application,
        test_aiohttp: Callable[..., Awaitable[TestClient]],
        mocker: MockerFixture,
):
    client = await test_aiohttp(app)
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
