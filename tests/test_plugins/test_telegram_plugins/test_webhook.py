import py.path
import pytest
from aiogram import Bot, Dispatcher
from pytest_mock import MockerFixture

from glQiwiApi.core.dispatcher.webhooks.config import ApplicationConfig
from glQiwiApi.plugins.telegram.webhook import (
    DEFAULT_TELEGRAM_WEBHOOK_PATH,
    DEFAULT_TELEGRAM_WEBHOOK_PATH_PREFIX,
    TelegramWebhookPlugin,
)
from glQiwiApi.utils.certificates import SSLCertificate, get_or_generate_self_signed_certificate


@pytest.fixture()
def self_signed_certificate(tmpdir: py.path.local) -> SSLCertificate:
    tmpdir.mkdir("test_certificates")
    path_to_cert = tmpdir.join("cert.pem")
    path_to_pkey = tmpdir.join("pkey.pem")
    return get_or_generate_self_signed_certificate(
        hostname="45.138.24.80", cert_path=path_to_cert, pkey_path=path_to_pkey
    )


async def test_webhook_plugin_install(
    mocker: MockerFixture, self_signed_certificate: SSLCertificate
):
    bot = Bot("32423:dfgd", validate_token=False)

    async def set_webhook_stub(*args, **kwargs):
        pass

    bot.set_webhook = set_webhook_stub
    spy = mocker.spy(bot, "set_webhook")
    dispatcher = Dispatcher(bot)

    plugin = TelegramWebhookPlugin(
        dispatcher,
        host="localhost",
        app_config=ApplicationConfig(ssl_certificate=self_signed_certificate),
    )
    run_app_mock = mocker.patch("glQiwiApi.plugins.telegram.webhook.run_app", autospec=True)
    await plugin.install(ctx={})

    expected_webhook_url = (
        "localhost"  # noqa
        + DEFAULT_TELEGRAM_WEBHOOK_PATH_PREFIX  # noqa
        + DEFAULT_TELEGRAM_WEBHOOK_PATH.format(token="32423:dfgd")  # noqa
    )
    spy.assert_awaited_once_with(
        url=expected_webhook_url, certificate=self_signed_certificate.as_input_file()
    )
    run_app_mock.assert_called_once()
