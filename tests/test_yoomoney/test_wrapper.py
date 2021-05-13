import asyncio
import datetime
from typing import Dict

import pytest

from glQiwiApi import YooMoneyAPI, types
from glQiwiApi.types import OperationType

pytestmark = pytest.mark.asyncio


@pytest.fixture(name='api')
async def api_fixture(yoo_credentials: Dict[str, str]):
    """ Api fixture """
    _wrapper = YooMoneyAPI(**yoo_credentials)
    yield _wrapper
    await _wrapper.close()


async def test_get_balance(api: YooMoneyAPI):
    async with api:
        balance = await api.balance

    assert isinstance(balance, float)


@pytest.mark.parametrize("payload", [
    {},
    {
        "records": 10,
    },
    {
        "records": 50,
        "operation_types": [OperationType.PAYMENT, OperationType.DEPOSITION]
    },
    {
        "records": 40,
        "operation_types": [OperationType.PAYMENT]
    },
    {
        "records": 80,
        "operation_types": [OperationType.PAYMENT, OperationType.DEPOSITION],
        "start_date": datetime.datetime.now() - datetime.timedelta(days=80),
        "end_date": datetime.datetime.now()
    }
])
async def test_get_transactions(api: YooMoneyAPI, payload: dict):
    async with api:
        transactions = await api.transactions(**payload)

    assert all(isinstance(txn, types.Operation) for txn in transactions)


async def test_account_info(api: YooMoneyAPI):
    async with api:
        info = await api.account_info

    assert isinstance(info, types.AccountInfo)


@pytest.mark.parametrize("operation_id", [
    "672180330623679897", "671568515431002412"
])
async def test_get_transaction_info(api: YooMoneyAPI, operation_id: str):
    async with api:
        transaction = await api.transaction_info(operation_id)
    assert isinstance(transaction, types.OperationDetails)


@pytest.mark.parametrize("payload", [
    {"amount": 2},
    {
        "amount": 2,
        "transaction_type": "out"
    },
    {
        "amount": 2,
        "transaction_type": "out",
        "rows_num": 20
    },
    {
        "amount": 2,
        "transaction_type": "out",
        "rows_num": 20,
        "recipient": "4100116633099701"
    }
])
async def test_check_transaction(api: YooMoneyAPI, payload: dict):
    async with api:
        result = await api.check_transaction(**payload)

    assert isinstance(result, bool)


async def test_send_and_check_txn(api: YooMoneyAPI):
    async with api:
        payload = {
            "amount": 2,
            "comment": "unit_test"
        }
        await api.send(
            to_account="4100116633099701",
            **payload
        )
        answer = await api.check_transaction(
            **payload,
            transaction_type="out"
        )
    assert answer is True
