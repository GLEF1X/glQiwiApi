from aiohttp import web
from aiohttp.pytest_plugin import AiohttpClient
from aiohttp.test_utils import TestClient
from aiohttp.web_app import Application
from aiohttp.web_request import Request

from glQiwiApi.core.event_fetching.dispatcher import QiwiDispatcher
from glQiwiApi.core.event_fetching.webhooks.app import configure_app
from glQiwiApi.core.event_fetching.webhooks.config import EncryptionConfig, WebhookConfig
from glQiwiApi.core.event_fetching.webhooks.middlewares.ip import ip_filter_middleware
from glQiwiApi.core.event_fetching.webhooks.services.security.ip import IPFilter
from tests.unit.test_dispatcher.mocks import WebhookTestData


class TestAiohttpServer:
    def test_configure_app(self, test_data: WebhookTestData):
        app = Application()

        dp = QiwiDispatcher()
        configure_app(
            dp,
            app,
            WebhookConfig(
                encryption=EncryptionConfig(
                    secret_p2p_key="", base64_encryption_key=test_data.base64_key_to_compare_hash
                )
            ),
        )

        assert len(app.router.routes()) == 2

    async def test_ip_middleware(self, aiohttp_client: AiohttpClient):
        app = Application()
        ip_filter = IPFilter.default()
        app.middlewares.append(ip_filter_middleware(ip_filter))

        async def handler(_: Request):
            return web.json_response({"ok": True})

        app.router.add_route("POST", "/webhook", handler)
        client: TestClient = await aiohttp_client(app)

        resp = await client.post("/webhook")
        assert resp.status == 401

        resp = await client.post("/webhook", headers={"X-Forwarded-For": "79.142.16.2"})
        assert resp.status == 200

        resp = await client.post(
            "/webhook", headers={"X-Forwarded-For": "79.142.16.2,91.213.51.238"}
        )
        assert resp.status == 200
