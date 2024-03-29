import pytest

from tests.unit.test_event_fetching.mocks import (
    MOCK_BILL_WEBHOOK_RAW_DATA,
    MOCK_TRANSACTION_WEBHOOK_RAW_DATA,
    TEST_BASE64_WEBHOOK_KEY,
    WebhookTestData,
)


@pytest.fixture()
def test_data() -> WebhookTestData:
    return WebhookTestData(
        bill_webhook_json=MOCK_BILL_WEBHOOK_RAW_DATA,
        base64_key_to_compare_hash=TEST_BASE64_WEBHOOK_KEY,
        transaction_webhook_json=MOCK_TRANSACTION_WEBHOOK_RAW_DATA,
    )
