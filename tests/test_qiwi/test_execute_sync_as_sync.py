import datetime
import time
import uuid
from typing import Dict

import pytest

from glQiwiApi import QiwiWrapper, execute_async_as_sync, base_types
from glQiwiApi.qiwi.types import Bill


@pytest.fixture(name="api_stub")
def sync_api_fixture(credentials: Dict[str, str], capsys):
    _wrapper = QiwiWrapper(**credentials)
    yield _wrapper


def test_sync_get_balance(api_stub: QiwiWrapper):
    result = execute_async_as_sync(api_stub.get_balance)
    assert isinstance(result, base_types.AmountWithCurrency)


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
def test_sync_create_p2p_bill(api_stub: QiwiWrapper, params: dict):
    result = execute_async_as_sync(api_stub.create_p2p_bill, **params)
    assert isinstance(result, Bill) is True
