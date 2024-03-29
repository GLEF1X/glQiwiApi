import pytest
from aiogram import Bot, Dispatcher
from pytest_mock import MockerFixture

from glQiwiApi.plugins.aiogram.polling import AiogramPollingPlugin


class TestPollingPlugin:
    @pytest.mark.skipif(
        'sys.version_info <= (3, 8)',
        reason="required functionality of pytest-mock doesn't work for this test on python <= 3.8",
    )
    async def test_install_telegram_polling_plugin(self, mocker: MockerFixture):
        dispatcher = Dispatcher(Bot(token='231:23dfgd', validate_token=False))
        start_polling_mock_method = mocker.AsyncMock(spec=dispatcher.start_polling)

        dispatcher.start_polling = start_polling_mock_method
        plugin = AiogramPollingPlugin(dispatcher=dispatcher)
        await plugin.install(ctx={})

        start_polling_mock_method.assert_awaited_once()

    async def test_shutdown_polling_plugin(self, mocker: MockerFixture):
        dispatcher = Dispatcher(Bot(token='231:23dfgd', validate_token=False))
        shutdown_mock_method = mocker.Mock(spec=dispatcher.stop_polling)
        dispatcher.stop_polling = shutdown_mock_method
        plugin = AiogramPollingPlugin(dispatcher=dispatcher)
        await plugin.shutdown()

        shutdown_mock_method.assert_called_once()
