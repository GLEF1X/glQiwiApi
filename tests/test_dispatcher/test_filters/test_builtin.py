import pytest

from glQiwiApi import types
from glQiwiApi.core.dispatcher._builtin_filters import BillFilter, TransactionFilter, ErrorFilter
from tests.test_dispatcher.mocks import MOCK_TRANSACTION_WEBHOOK_RAW_DATA, MOCK_BILL_WEBHOOK_RAW_DATA
from tests.types.dataset import TXN_RAW_DATA

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "event", [types.BillWebhook.parse_raw(MOCK_BILL_WEBHOOK_RAW_DATA)]
)
async def test_bill_webhook_filter(event):
    assert await BillFilter().check(event)


@pytest.mark.parametrize(
    "event",
    [
        types.TransactionWebhook.parse_raw(MOCK_TRANSACTION_WEBHOOK_RAW_DATA),
        types.Transaction.parse_raw(TXN_RAW_DATA),
    ],
)
async def test_transaction_webhook_filter(event):
    assert await TransactionFilter().check(event)


async def test_error_filter_without_certain_default_exception():
    assert await ErrorFilter().check(ValueError())


async def test_error_filter_with_certain_default_exc():
    assert await ErrorFilter(exception=OSError).check(OSError())


async def test_reraise_exception_if_default_exc_not_equal_to_transmitted():
    with pytest.raises(ValueError):
        await ErrorFilter(exception=OSError).check(ValueError())
