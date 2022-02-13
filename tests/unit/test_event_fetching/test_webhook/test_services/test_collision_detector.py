from __future__ import annotations

import pytest

from glQiwiApi.core.event_fetching.webhooks.services.collision_detector import (
    HashBasedCollisionDetector,
    UnexpectedCollision,
    UnhashableObjectError,
)
from glQiwiApi.qiwi.clients.wallet.types import TransactionWebhook


class UnhashableTestClass:
    def __eq__(self, other):
        return False


@pytest.fixture(name="detector")
def collision_detector_fixture() -> HashBasedCollisionDetector:
    return HashBasedCollisionDetector()


def test_add_processed_event(
    test_webhook: TransactionWebhook, detector: HashBasedCollisionDetector
):
    detector.remember_processed_object(test_webhook)
    assert hash(test_webhook) in detector.already_processed_object_hashes


def test_collision_error_raise(
    test_webhook: TransactionWebhook, detector: HashBasedCollisionDetector
):
    detector.remember_processed_object(test_webhook)
    with pytest.raises(UnexpectedCollision):
        detector.remember_processed_object(test_webhook)


def test_fail_if_object_is_unhashable(
    test_webhook: TransactionWebhook, detector: HashBasedCollisionDetector
):
    with pytest.raises(UnhashableObjectError):
        detector.remember_processed_object(UnhashableTestClass())
