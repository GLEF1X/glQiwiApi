import pytest

from glQiwiApi import types
from glQiwiApi.core.dispatcher._builtin_filters import BillFilter, TransactionFilter
from tests.types.dataset import NOTIFICATION_RAW_DATA, WEBHOOK_RAW_DATA, TXN_RAW_DATA


@pytest.mark.parametrize(
    "update", [types.Notification.parse_raw(NOTIFICATION_RAW_DATA)]
)
@pytest.mark.asyncio
async def test_bill_webhook_filter(update):
    assert await BillFilter().check(update)


@pytest.mark.parametrize(
    "update",
    [
        types.WebHook.parse_raw(WEBHOOK_RAW_DATA),
        types.Transaction.parse_raw(TXN_RAW_DATA),
    ],
)
@pytest.mark.asyncio
async def test_transaction_webhook_filter(update):
    assert await TransactionFilter().check(update)
