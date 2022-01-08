import pytest

from glQiwiApi import QiwiWallet, base_types
from glQiwiApi.core.synchronous.adapter import execute_async_as_sync
from tests.types.dataset import QIWI_WALLET_CREDENTIALS


@pytest.fixture(name="api_stub")
async def sync_api_fixture():
    _wrapper = QiwiWallet(**QIWI_WALLET_CREDENTIALS)
    yield _wrapper
    await _wrapper.close()


def test_sync_get_balance(api_stub: QiwiWallet):
    result = execute_async_as_sync(api_stub.get_balance)
    assert isinstance(result, base_types.AmountWithCurrency)
