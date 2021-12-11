import asyncio
import logging
from asyncio import AbstractEventLoop

import pytest
from _pytest.logging import LogCaptureFixture
from aiohttp.pytest_plugin import AiohttpClient
from aiohttp.test_utils import TestClient
from aiohttp.web_app import Application

from glQiwiApi import types
from glQiwiApi.core import QiwiTransactionWebhookView
from glQiwiApi.core.dispatcher.implementation import Dispatcher
from glQiwiApi.core.dispatcher.webhooks.dto.errors import WebhookAPIError
from glQiwiApi.core.dispatcher.webhooks.services.collision_detector import HashBasedCollisionDetector
from glQiwiApi.core.dispatcher.webhooks.utils import inject_dependencies
from tests.test_dispatcher.mocks import WebhookTestData

pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def application(test_data: WebhookTestData, loop: AbstractEventLoop):
    dp = Dispatcher()
    app = Application(loop=loop)
    handler_event = asyncio.Event()

    app["handler_event"] = handler_event

    @dp.transaction_handler()
    async def handle_txn_webhook(_: types.TransactionWebhook):
        handler_event.set()

    app.router.add_view(
        handler=inject_dependencies(QiwiTransactionWebhookView, {
            "event_cls": types.TransactionWebhook,
            "dispatcher": dp,
            "secret_key": test_data.base64_key_to_compare_hash,
            "collision_detector": HashBasedCollisionDetector(),
        }),
        path="/webhook",
        name="txn_webhook"
    )
    return app


class TestTxnWebhookView:

    async def test_with_right_payload(self, aiohttp_client: AiohttpClient,
                                      test_data: WebhookTestData, application: Application):
        client: TestClient = await aiohttp_client(application)
        response = await client.post("/webhook", json=test_data.transaction_webhook_json)

        assert response.status == 200
        assert await response.text() == "ok"
        assert application["handler_event"].is_set() is True

    async def test_with_invalid_payload(self, aiohttp_client: AiohttpClient,
                                        test_data: WebhookTestData, application: Application,
                                        caplog: LogCaptureFixture):
        client: TestClient = await aiohttp_client(application)

        txn = types.TransactionWebhook.parse_raw(test_data.transaction_webhook_json)

        # Copy transaction to update hash to fake and test that service will send unsuccessfull response
        fake_transaction = txn.copy(
            update={
                "hash": "fake hash",
                "payment": {
                    **txn.payment.dict(by_alias=True),
                    "sum": {
                        "currency": txn.payment.sum.currency.code,
                        "amount": txn.payment.sum.amount
                    },
                    "total": {
                        "currency": txn.payment.sum.currency.code,
                        "amount": txn.payment.sum.amount

                    }
                },
                "hookId": txn.id,
                "test": txn.is_experimental
            },
            deep=True
        )

        with caplog.at_level(logging.DEBUG, logger="glQiwiApi.webhooks.transaction"):
            response = await client.post("/webhook", json=fake_transaction.json(by_alias=True))
            assert "Request has being blocked due to invalid signature" in caplog.text

        assert response.status == 400
        assert WebhookAPIError.parse_obj(await response.json()).status == "Invalid hash of transaction."
        assert application["handler_event"].is_set() is False

    async def test_logs_when_collision_was(self, aiohttp_client: AiohttpClient, test_data: WebhookTestData,
                                           application: Application, caplog: LogCaptureFixture):
        client: TestClient = await aiohttp_client(application)
        handler_event: asyncio.Event = application["handler_event"]

        resp = await client.post("/webhook", json=test_data.transaction_webhook_json)

        assert resp.status == 200
        assert handler_event.is_set() is True

        handler_event.clear()

        with caplog.at_level(level=logging.DEBUG, logger="glQiwiApi.webhooks.base"):
            response_when_send_the_same_txn = await client.post("/webhook",
                                                                json=test_data.transaction_webhook_json)
            assert "Detect collision on event" in caplog.text

        assert response_when_send_the_same_txn.status == 200
        assert handler_event.is_set() is False

    async def test_404_resp_if_payload_is_invalid(self, aiohttp_client: AiohttpClient,
                                                  test_data: WebhookTestData,
                                                  application: Application):
        client: TestClient = await aiohttp_client(application)
        handler_event: asyncio.Event = application["handler_event"]

        resp = await client.post("/webhook", json="{'hello': 'world'}")

        assert resp.status == 400
        assert WebhookAPIError.parse_obj(await resp.json()).status == "Validation error"
        assert handler_event.is_set() is False
