import asyncio
from asyncio import AbstractEventLoop

import pytest
from aiohttp.pytest_plugin import AiohttpClient
from aiohttp.test_utils import TestClient
from aiohttp.web_app import Application

from glQiwiApi import types
from glQiwiApi.core import QiwiBillWebhookView
from glQiwiApi.core.dispatcher.implementation import Dispatcher
from glQiwiApi.core.dispatcher.webhooks.services.collision_detector import (
    HashBasedCollisionDetector,
)
from glQiwiApi.core.dispatcher.webhooks.utils import inject_dependencies
from tests.test_dispatcher.mocks import WebhookTestData

pytestmark = pytest.mark.asyncio


class QiwiBillWebhookViewWithoutSignatureValidation(QiwiBillWebhookView):
    def _validate_event_signature(self, update: types.BillWebhook) -> None:
        """
        We cannot test, because we have not X-Api-Signature-SHA256 for webhook.
        I have tested it manually on remote host
        """


class TestBillWebhookView:
    async def test_with_right_payload(
        self, aiohttp_client: AiohttpClient, test_data: WebhookTestData, loop: AbstractEventLoop
    ):
        dp = Dispatcher()
        app = Application()
        event_handled_by_handler = asyncio.Event()

        @dp.bill_handler()
        async def handle_bill_webhook(_: types.BillWebhook):
            event_handled_by_handler.set()

        app.router.add_view(
            handler=inject_dependencies(
                QiwiBillWebhookViewWithoutSignatureValidation,
                {
                    "event_cls": types.BillWebhook,
                    "dispatcher": dp,
                    "encryption_key": test_data.base64_key_to_compare_hash,
                    "collision_detector": HashBasedCollisionDetector(),
                },
            ),
            path="/webhook",
            name="bill_webhook",
        )

        client: TestClient = await aiohttp_client(app)
        response = await client.post("/webhook", json=test_data.bill_webhook_json)

        assert response.status == 200
        assert await response.json() == {"error": "0"}

        assert event_handled_by_handler.is_set() is True
