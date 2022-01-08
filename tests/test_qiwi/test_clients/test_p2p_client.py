import datetime
import uuid

import pytest

from glQiwiApi import QiwiP2PClient
from glQiwiApi.qiwi.types import (
    Bill,
)
from tests.types.dataset import SECRET_P2P_CREDENTIALS

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="api")
async def api_fixture():
    _wrapper = QiwiP2PClient(**SECRET_P2P_CREDENTIALS)
    yield _wrapper
    await _wrapper.close()


@pytest.mark.parametrize(
    "payload",
    [
        {"amount": 1},
        {"amount": 1, "comment": "test_comment"},
        {
            "amount": 1,
            "comment": "test_comment",
            "expire_at": datetime.datetime.now() + datetime.timedelta(hours=5),
        },
        {
            "amount": 1,
            "comment": "test_comment",
            "expire_at": datetime.datetime.now() + datetime.timedelta(hours=5),
            "bill_id": str(uuid.uuid4()),
        },
    ],
)
async def test_create_p2p_bill(api: QiwiP2PClient, payload: dict):
    result = await api.create_p2p_bill(**payload)
    assert isinstance(result, Bill)
    assert payload["amount"] == result.amount.value


async def test_check_p2p_bill_status(api: QiwiP2PClient):
    test_bill = await api.create_p2p_bill(amount=1)
    result = await api.get_bill_status(bill_id=test_bill.id)
    assert isinstance(result, str)


async def test_get_bill_by_id(api: QiwiP2PClient):
    test_bill = await api.create_p2p_bill(amount=1)
    assert await api.get_bill_by_id(test_bill.id) == test_bill


async def test_check_p2p_on_object(api: QiwiP2PClient):
    bill = await api.create_p2p_bill(amount=1)
    assert isinstance(bill, Bill)
    result = await bill.check()

    assert isinstance(result, bool)


async def test_reject_p2p_bill(api: QiwiP2PClient):
    b = await api.create_p2p_bill(amount=1)
    rejected_bill = await api.reject_p2p_bill(b.id)
    assert isinstance(rejected_bill, Bill)
