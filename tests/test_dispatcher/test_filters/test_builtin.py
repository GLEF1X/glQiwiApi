import pytest

from glQiwiApi import types
from glQiwiApi.core.dispatcher._builtin_filters import BillFilter, TransactionFilter
from tests.test_dispatcher.mocks import MOCK_TRANSACTION_WEBHOOK_RAW_DATA, MOCK_BILL_WEBHOOK_RAW_DATA
from tests.types.dataset import TXN_RAW_DATA

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "update", [types.BillWebhook.parse_raw(MOCK_BILL_WEBHOOK_RAW_DATA)]
)
async def test_bill_webhook_filter(update):
    assert await BillFilter().check(update)


@pytest.mark.parametrize(
    "update",
    [
        types.TransactionWebhook.parse_raw(MOCK_TRANSACTION_WEBHOOK_RAW_DATA),
        types.Transaction.parse_raw(TXN_RAW_DATA),
    ],
)
async def test_transaction_webhook_filter(update):
    assert await TransactionFilter().check(update)
