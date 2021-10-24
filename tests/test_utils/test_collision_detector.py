from __future__ import annotations

import pytest

from glQiwiApi.core.dispatcher.webhooks.collision_detectors import HashBasedCollisionDetector, UnexpectedCollision
from glQiwiApi.types import WebHook


@pytest.fixture(name="detector")
def collision_detector_fixture() -> HashBasedCollisionDetector:
    return HashBasedCollisionDetector()


def test_add_processed_event(test_webhook: WebHook, detector: HashBasedCollisionDetector):
    detector.remember_processed_object(test_webhook)
    assert hash(test_webhook) in detector.already_processed_object_hashes


def test_collision_error_raise(test_webhook: WebHook, detector: HashBasedCollisionDetector):
    detector.remember_processed_object(test_webhook)
    with pytest.raises(UnexpectedCollision):
        detector.remember_processed_object(test_webhook)
