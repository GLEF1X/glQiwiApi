from __future__ import annotations

import datetime
import pathlib
import uuid
from typing import Dict

import pytest

from glQiwiApi import SyncAdaptedQiwi, APIError
from glQiwiApi.core.synchronous.model_adapter import AdaptedBill
from glQiwiApi.types import (
    Transaction,
    Limit,
    Card,
    QiwiAccountInfo,
    Statistic,
    Commission,
    CrossRate,
    TransactionType,
)


@pytest.fixture(name="api_adapter")
def sync_api_fixture(credentials: Dict[str, str]):
    _wrapper = SyncAdaptedQiwi(**credentials)
    yield _wrapper


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
def test_create_p2p_bill(api_adapter: SyncAdaptedQiwi, params):
    adapted_bill = api_adapter.create_p2p_bill(**params)
    assert isinstance(adapted_bill, AdaptedBill)


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
def test_p2p_bill_check(api_adapter: SyncAdaptedQiwi, params):
    adapted_bill = api_adapter.create_p2p_bill(**params)
    assert isinstance(adapted_bill.check(), bool)


@pytest.mark.parametrize(
    "payload",
    [
        {"rows": 50},
        {"rows": 50, "operation": TransactionType.IN},
        {
            "rows": 50,
            "operation": TransactionType.IN,
            "start_date": datetime.datetime.now() - datetime.timedelta(days=50),
            "end_date": datetime.datetime.now(),
        },
    ],
)
def test_transactions(api_adapter: SyncAdaptedQiwi, payload):
    transactions = api_adapter.transactions(**payload)
    assert all(isinstance(txn, Transaction) for txn in transactions)


@pytest.mark.parametrize("rows", [5, 10, 50])
def test_get_bills(api_adapter: SyncAdaptedQiwi, rows: int):
    bills = api_adapter.retrieve_bills(rows=rows)
    assert isinstance(bills, list)


@pytest.mark.parametrize(
    "payload",
    [{"transaction_id": 21601937643, "transaction_type": TransactionType.OUT}],
)
def test_transaction_info(api_adapter: SyncAdaptedQiwi, payload: dict):
    res = api_adapter.transaction_info(**payload)
    assert isinstance(res, Transaction)


def check_restriction(api_adapter: SyncAdaptedQiwi):
    res = api_adapter.check_restriction()
    assert isinstance(res, list)


def test_get_limits(api_adapter: SyncAdaptedQiwi):
    res = api_adapter.get_limits()

    assert isinstance(res, dict)
    assert all([isinstance(t, list) for t in res.values()])


def test_get_list_of_cards(api_adapter: SyncAdaptedQiwi):
    result = api_adapter.get_list_of_cards()
    assert all(isinstance(c, Card) for c in result)


def test_get_receipt(api_adapter: SyncAdaptedQiwi):
    payload = {"transaction_id": 21601937643, "transaction_type": TransactionType.OUT}
    assert isinstance(api_adapter.get_receipt(**payload), bytes)


def test_account_info(api_adapter: SyncAdaptedQiwi):
    info = api_adapter.get_account_info()
    assert isinstance(info, QiwiAccountInfo)


@pytest.mark.parametrize(  # noqa
    "payload",
    [
        {
            "start_date": datetime.datetime.now() - datetime.timedelta(days=50),
            "end_date": datetime.datetime.now(),
        },
        {
            "start_date": datetime.datetime.now() - datetime.timedelta(days=50),
            "end_date": datetime.datetime.now(),
            "operation": TransactionType.IN,
        },
        {
            "start_date": datetime.datetime.now() - datetime.timedelta(days=50),
            "end_date": datetime.datetime.now(),
            "operation": TransactionType.OUT,
        },
        {
            "start_date": datetime.datetime.now() - datetime.timedelta(days=50),
            "end_date": datetime.datetime.now(),
            "operation": TransactionType.ALL,
        },
        {
            "start_date": datetime.datetime.now() - datetime.timedelta(days=50),
            "end_date": datetime.datetime.now(),
            "operation": TransactionType.ALL,
            "sources": ["QW_RUB"],
        },
        {
            "start_date": datetime.datetime.now() - datetime.timedelta(days=50),
            "end_date": datetime.datetime.now(),
            "operation": TransactionType.ALL,
            "sources": ["QW_RUB", "QW_EUR", "QW_USD"],
        },
    ],
)
def test_fetch_statistic(api_adapter: SyncAdaptedQiwi, payload: dict):
    result = api_adapter.fetch_statistics(**payload)

    assert isinstance(result, Statistic)


def test_check_p2p_bill_status(api_adapter: SyncAdaptedQiwi):
    result = api_adapter.check_p2p_bill_status(
        bill_id="8d517426-920a-4711-86c2-4267784bf901"
    )
    assert isinstance(result, str)


@pytest.mark.parametrize(
    "payload",
    [
        {"to_account": "+380985272064", "pay_sum": 999},
        {"to_account": "4890494756089082", "pay_sum": 1},
    ],
)
def test_commission(api_adapter: SyncAdaptedQiwi, payload: dict):
    result = api_adapter.calc_commission(**payload)
    assert isinstance(result, Commission)


def test_get_cross_rates(api_adapter: SyncAdaptedQiwi):
    cross_rates = api_adapter.get_cross_rates()
    assert all(isinstance(rate, CrossRate) for rate in cross_rates)


def test_buy_qiwi_master(api_adapter: SyncAdaptedQiwi):
    with pytest.raises(APIError) as ex:  # not enough money on qiwi wallet to buy it
        api_adapter.buy_qiwi_master()
    assert ex.value.status_code == 400
