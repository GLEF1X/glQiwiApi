from __future__ import annotations

from ssl import SSLContext

import pytest
from aiogram import Dispatcher
from aiohttp import web
from pytest_mock import MockerFixture

from glQiwiApi.plugins.telegram.webhook import TelegramWebhookPlugin

pytestmark = pytest.mark.asyncio


class EventLoopStub:
    def run_until_complete(self, coro_or_future):
        coro_or_future.close()  # to avoid RuntimeWarning


@pytest.fixture(name="tg_webhook_proxy")
async def tg_webhook_proxy_fixture(mocker: MockerFixture):
    mocker.MagicMock()
    tg_proxy = TelegramWebhookPlugin(
            Dispatcher(bot_mock),
            webhook_domain="",
            ssl_certificate=SSLContext(),
    )  # noqa
    yield tg_proxy


async def test_telegram_webhook_proxy(tg_webhook_proxy: TelegramWebhookPlugin):
    web_app = await tg_webhook_proxy.incline(ctx=dict(app=web.Application()))
    assert isinstance(web_app, web.Application)
