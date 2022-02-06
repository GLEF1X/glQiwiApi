from typing import AsyncIterator

import pytest

from glQiwiApi import QiwiWallet
from glQiwiApi.core.synchronous.adapter import execute_async_as_sync
from glQiwiApi.types.amount import AmountWithCurrency
from tests.settings import QIWI_WALLET_CREDENTIALS


@pytest.fixture(name="wallet")
async def sync_api_fixture() -> AsyncIterator[QiwiWallet]:
    async with QiwiWallet(**QIWI_WALLET_CREDENTIALS) as wallet:
        yield wallet


def test_sync_get_balance(wallet: QiwiWallet) -> None:
    result = execute_async_as_sync(wallet.get_balance)
    assert isinstance(result, AmountWithCurrency)
