import datetime
from typing import Any, AsyncIterator, Dict

import pytest

from glQiwiApi import YooMoneyAPI
from glQiwiApi.yoo_money.types import AccountInfo, Operation, OperationDetails
from tests.settings import YOO_MONEY_CREDENTIALS, YOO_MONEY_TEST_CLIENT_ID

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="api")
async def api_fixture() -> AsyncIterator[YooMoneyAPI]:
    async with YooMoneyAPI(**YOO_MONEY_CREDENTIALS) as api:
        yield api


async def test_get_balance(api: YooMoneyAPI) -> None:
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
async def test_get_transactions(api: YooMoneyAPI, payload: Dict[str, Any]) -> None:
    transactions = await api.operation_history(**payload)
    assert all(isinstance(txn, Operation) for txn in transactions)


async def test_build_url_for_auth() -> None:
    link = await YooMoneyAPI.build_url_for_auth(
        scopes=["account-info", "operation-history", "operation-details", "payment-p2p"],
        client_id=YOO_MONEY_TEST_CLIENT_ID,
    )
    assert isinstance(link, str)


async def test_account_info(api: YooMoneyAPI) -> None:
    info = await api.retrieve_account_info()
    assert isinstance(info, AccountInfo)


@pytest.mark.parametrize("operation_id", ["672180330623679897", "671568515431002412"])
async def test_get_transaction_info(api: YooMoneyAPI, operation_id: str) -> None:
    transaction = await api.operation_details(operation_id)
    assert isinstance(transaction, OperationDetails)


@pytest.mark.skip()
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
async def test_check_if_operation_exists(api: YooMoneyAPI, payload: Dict[str, Any]) -> None:
    result = await api.check_if_operation_exists(**payload)
    assert isinstance(result, bool)


@pytest.mark.skip()
async def test_send_and_check_txn(api: YooMoneyAPI) -> None:
    payload = {"amount": 2, "comment": "unit_test"}
    await api.transfer_money(to_account="4100116633099701", **payload)
    answer = await api.check_if_operation_exists(**payload, operation_types=["out"])
    assert answer is True
