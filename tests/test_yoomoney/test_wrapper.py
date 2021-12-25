import datetime
from typing import Dict

import pytest

from glQiwiApi import YooMoneyAPI
from glQiwiApi.yoo_money.types import Operation, AccountInfo, OperationDetails

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="api")
async def api_fixture(yoo_credentials: Dict[str, str]):
    """Api fixture"""
    _wrapper = YooMoneyAPI(**yoo_credentials)
    yield _wrapper
    await _wrapper.close()


async def test_get_balance(api: YooMoneyAPI):
    balance = await api.get_balance()
    assert isinstance(balance, float)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {
            "records": 10,
        },
        {
            "records": 50,
            "operation_types": ["PAYMENT", "DEPOSITION"],
        },
        {"records": 40, "operation_types": ["PAYMENT"]},
        {
            "records": 80,
            "operation_types": ["PAYMENT", "DEPOSITION"],
            "start_date": datetime.datetime.now() - datetime.timedelta(days=80),
            "end_date": datetime.datetime.now(),
        },
    ],
)
async def test_get_transactions(api: YooMoneyAPI, payload: dict):
    transactions = await api.operation_history(**payload)
    assert all(isinstance(txn, Operation) for txn in transactions)


async def test_account_info(api: YooMoneyAPI):
    info = await api.retrieve_account_info()
    assert isinstance(info, AccountInfo)


@pytest.mark.parametrize("operation_id", ["672180330623679897", "671568515431002412"])
async def test_get_transaction_info(api: YooMoneyAPI, operation_id: str):
    transaction = await api.operation_info(operation_id)
    assert isinstance(transaction, OperationDetails)


@pytest.mark.skip
@pytest.mark.parametrize(
    "payload",
    [
        {"amount": 2},
        {"amount": 2, "operation_type": "out"},
        {"amount": 2, "operation_type": "out", "rows": 20},
        {
            "amount": 2,
            "operation_type": "out",
            "rows": 20,
            "recipient": "4100116633099701",
        },
    ],
)
async def test_check_transaction(api: YooMoneyAPI, payload: dict):
    result = await api.is_exists_transaction_with_similar_properties(**payload)
    assert isinstance(result, bool)


async def test_send_and_check_txn(api: YooMoneyAPI):
    payload = {"amount": 2, "comment": "unit_test"}
    await api.send(to_account="4100116633099701", **payload)
    answer = await api.is_exists_transaction_with_similar_properties(
        **payload, operation_types=["out"]
    )
    assert answer is True
