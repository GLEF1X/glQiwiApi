import datetime
import uuid
from typing import Dict

import pytest

from glQiwiApi import QiwiWrapper, execute_async_as_sync
from glQiwiApi import types


@pytest.fixture(name="api")
def sync_api_fixture(credentials: Dict[str, str]):
    _wrapper = QiwiWrapper(**credentials)
    yield _wrapper


def test_sync_get_balance(api: QiwiWrapper):
    result = execute_async_as_sync(api.get_balance)
    assert isinstance(result, types.Sum)


@pytest.mark.parametrize(
    "params",
    [
        {"amount": 1},
        {"amount": 1, "comment": "test_comment"},
        {
            "amount": 1,
            "comment": "test_comment",
            "life_time": datetime.datetime.now() + datetime.timedelta(hours=5),
        },
        {
            "amount": 1,
            "comment": "test_comment",
            "life_time": datetime.datetime.now() + datetime.timedelta(hours=5),
            "bill_id": str(uuid.uuid4()),
        },
    ],
)
def test_sync_create_p2p_bill(api: QiwiWrapper, params: dict):
    result = execute_async_as_sync(api.create_p2p_bill, **params)
    assert isinstance(result, types.Bill)
