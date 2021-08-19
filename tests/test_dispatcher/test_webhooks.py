import asyncio
from typing import Awaitable, Callable

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient
from pytest_mock import MockerFixture

from glQiwiApi.core.dispatcher.webhooks.config import (
    DEFAULT_QIWI_BILLS_WEBHOOK_PATH,
    DEFAULT_QIWI_WEBHOOK_PATH,
)
from glQiwiApi.core.dispatcher.webhooks.utils import check_ip  # NOQA
from tests.types.dataset import NOTIFICATION_RAW_DATA, WEBHOOK_RAW_DATA

pytestmark = pytest.mark.asyncio


async def test_bill_webhook_handler(
    app: web.Application,
    test_aiohttp: Callable[..., Awaitable[TestClient]],
    mocker: MockerFixture,
):
    client = await test_aiohttp(app)
    bill_event: asyncio.Event = app["bill_event"]
    mocker.patch(
        "glQiwiApi.core.dispatcher.webhooks.views.bill_view.QiwiBillWebView.validate_ip",
        return_value=None,
    )
    mocker.patch(
        "glQiwiApi.core.dispatcher.webhooks.views.bill_view.QiwiBillWebView._validate_event_signature",
        return_value=None,
    )
    bill_response = await client.post(
        path=DEFAULT_QIWI_BILLS_WEBHOOK_PATH, json=NOTIFICATION_RAW_DATA
    )
    assert bill_response.status == 200
    assert bill_event.is_set()


async def test_transaction_handler(
    app: web.Application,
    test_aiohttp: Callable[..., Awaitable[TestClient]],
    mocker: MockerFixture,
):
    client = await test_aiohttp(app)
    # skip ip validation
    mocker.patch(
        "glQiwiApi.core.dispatcher.webhooks.views.transaction_view.QiwiWebHookWebView.validate_ip",
        return_value=None,
    )
    transaction_response = await client.post(
        path=DEFAULT_QIWI_WEBHOOK_PATH, json=WEBHOOK_RAW_DATA
    )
    assert transaction_response.status == 200


async def test_check_ip_address():
    assert check_ip(ip_address="79.142.16.0")
    assert not check_ip(ip_address="127.0.0.1")
