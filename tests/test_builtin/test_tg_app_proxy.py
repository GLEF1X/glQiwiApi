from __future__ import annotations

from ssl import SSLContext

import pytest
from aiogram import Dispatcher, Bot
from aiohttp import web
from pytest_mock import MockerFixture

from glQiwiApi.builtin import TelegramWebhookProxy

pytestmark = pytest.mark.asyncio


class EventLoopStub:
    def run_until_complete(self, coro_or_future):
        coro_or_future.close()  # to avoid RuntimeWarning


@pytest.fixture(name="tg_webhook_proxy")
async def tg_webhook_proxy_fixture(mocker: MockerFixture):
    bot_mock = mocker.Mock(spec=Bot)
    tg_proxy = TelegramWebhookProxy(
        Dispatcher(bot_mock),
        webhook_domain="",
        ssl_certificate=SSLContext(),
        loop=EventLoopStub(),
    )  # noqa
    yield tg_proxy


async def test_telegram_webhook_proxy(tg_webhook_proxy: TelegramWebhookProxy):
    web_app = tg_webhook_proxy.setup(app=web.Application())
    assert isinstance(web_app, web.Application)
