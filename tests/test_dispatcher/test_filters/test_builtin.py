import pytest
from glQiwiApi.core.web_hooks.filter import (
    transaction_webhook_filter,
    bill_webhook_filter
)
from glQiwiApi import types
from tests.types.dataset import (
    NOTIFICATION_RAW_DATA,
    WEBHOOK_RAW_DATA,
    TXN_RAW_DATA
)


@pytest.mark.parametrize("update", [
    types.Notification.parse_raw(NOTIFICATION_RAW_DATA)
])
def test_bill_webhook_filter(update):
    assert bill_webhook_filter.function(update)


@pytest.mark.parametrize("update", [
    types.WebHook.parse_raw(WEBHOOK_RAW_DATA),
    types.Transaction.parse_raw(TXN_RAW_DATA)])
def test_transaction_webhook_filter(update):
    assert transaction_webhook_filter.function(update)
