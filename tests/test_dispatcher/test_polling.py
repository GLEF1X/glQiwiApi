from typing import Dict

import pytest
import timeout_decorator

from glQiwiApi import QiwiWrapper
from glQiwiApi import types


@pytest.fixture(name='credentials')
def credentials_fixture():
    """ credentials fixture """
    from ..types.dataset import API_DATA
    yield API_DATA


@pytest.mark.asyncio
@pytest.fixture(name='api')
async def api_fixture(credentials: Dict[str, str]):
    """ Api fixture """
    _wrapper = QiwiWrapper(**credentials)
    yield _wrapper
    await _wrapper.close()


async def _on_startup_callback(api: QiwiWrapper):
    from ..types.dataset import TO_WALLET_DATA
    await api.to_wallet(**TO_WALLET_DATA)


class TestPolling:

    @timeout_decorator.timeout(5)
    def _start_polling(self, api: QiwiWrapper):
        self._handled = False

        # Also, without decorators, you can do like this
        # api.dispatcher.register_transaction_handler(my_handler)
        @api.transaction_handler()
        async def my_handler(event: types.Transaction):
            self._handled = True
            assert isinstance(event, types.Transaction)

        api.start_polling(
            timeout=10,
            on_startup=_on_startup_callback
        )

    def test_polling(self, api: QiwiWrapper):
        try:
            self._start_polling(api)
        except timeout_decorator.TimeoutError:
            assert self._handled is True
