import datetime
import pathlib
import uuid
from typing import Dict, Union

import pytest
from glQiwiApi import types, InvalidData
from glQiwiApi import QiwiWrapper

pytestmark = pytest.mark.asyncio


@pytest.fixture(name='api')
async def api_fixture(credentials: Dict[str, str]):
    """ Api fixture """
    _wrapper = QiwiWrapper(**credentials)
    yield _wrapper
    await _wrapper.close()


async def test_get_balance(api: QiwiWrapper):
    from glQiwiApi.types.qiwi_types.currency_parsed import CurrencyModel
    async with api:
        result = await api.get_balance()
    assert isinstance(result, types.Sum)
    assert isinstance(result.currency, CurrencyModel)


@pytest.mark.parametrize(
    "payload",
    [
        {"rows_num": 50},
        {"rows_num": 50,
         "operation": "IN"},
        {
            "rows_num": 50,
            "operation": "IN",
            "start_date": datetime.datetime.now() - datetime.timedelta(
                days=50),
            "end_date": datetime.datetime.now()
        }
    ]
)
async def test_transactions(api: QiwiWrapper, payload: dict):
    async with api:
        result = await api.transactions(**payload)

    assert all(isinstance(t, types.Transaction) for t in result)


@pytest.mark.parametrize("payload", [
    {
        "transaction_id": 21601937643,
        "transaction_type": "OUT"
    }
])
async def test_transaction_info(api: QiwiWrapper, payload: dict):
    async with api:
        result = await api.transaction_info(**payload)

    assert isinstance(result, types.Transaction)


async def test_identification(api: QiwiWrapper):
    async with api:
        result = await api.identification
    assert isinstance(result, types.Identification)


@pytest.mark.parametrize("payload", [
    {
        "transaction_type": "OUT",
        "amount": 1
    },
    {
        "transaction_type": "OUT",
        "amount": 1,
        "sender": "+380985272064"
    },
    {
        "transaction_type": "OUT",
        "amount": 1,
        "sender": "+380985272064",
        "comment": "+comment+"
    }
])
async def test_check_transaction(api: QiwiWrapper, payload: dict):
    async with api:
        r = await api.check_transaction(**payload)
    assert r is True


async def test_get_limits(api: QiwiWrapper):
    async with api:
        result = await api.get_limits()

    assert isinstance(result, dict)
    assert all(isinstance(t, types.Limit) for t in result.values())


async def test_get_list_of_cards(api: QiwiWrapper):
    async with api:
        result = await api.get_list_of_cards()
    assert all(isinstance(c, types.Card) for c in result)


async def test_get_receipt_and_save(
        api: QiwiWrapper, path_to_dir: pathlib.Path
):
    from ..types.dataset import RECEIPT_FILE_NAME
    file_name = RECEIPT_FILE_NAME
    payload = {
        "transaction_id": 21601937643,
        "transaction_type": "OUT",
        "dir_path": path_to_dir,
    }
    async with api:
        await api.get_receipt(**payload, file_name=file_name)
    assert (path_to_dir / (file_name + ".pdf")).is_file()


async def test_account_info(api: QiwiWrapper):
    async with api:
        result = await api.account_info

    assert isinstance(result, types.QiwiAccountInfo)


@pytest.mark.parametrize("payload", [
    {
        "start_date": datetime.datetime.now() - datetime.timedelta(days=50),
        "end_date": datetime.datetime.now()
    },
    {
        "start_date": datetime.datetime.now() - datetime.timedelta(days=50),
        "end_date": datetime.datetime.now(),
        "operation": "IN"
    },
    {
        "start_date": datetime.datetime.now() - datetime.timedelta(days=50),
        "end_date": datetime.datetime.now(),
        "operation": "OUT"
    },
    {
        "start_date": datetime.datetime.now() - datetime.timedelta(days=50),
        "end_date": datetime.datetime.now(),
        "operation": "ALL"
    },
    {
        "start_date": datetime.datetime.now() - datetime.timedelta(days=50),
        "end_date": datetime.datetime.now(),
        "operation": "ALL",
        "sources": ["QW_RUB"]
    },
    {
        "start_date": datetime.datetime.now() - datetime.timedelta(days=50),
        "end_date": datetime.datetime.now(),
        "operation": "ALL",
        "sources": ["QW_RUB", "QW_EUR", "QW_USD"]
    }
])
async def test_fetch_statistic(api: QiwiWrapper, payload: dict):
    async with api:
        result = await api.fetch_statistics(**payload)

    assert isinstance(result, types.Statistic)


async def test_list_of_balances(api: QiwiWrapper):
    async with api:
        balances = await api.list_of_balances()

    assert all(isinstance(b, types.Account) for b in balances)


async def test_fail_fetch_statistic(api: QiwiWrapper):
    payload = {
        # Wrong start date
        "start_date": datetime.datetime.now() - datetime.timedelta(days=100),
        "end_date": datetime.datetime.now(),
        "operation": "OUT"
    }
    async with api:
        with pytest.raises(ValueError):
            await api.fetch_statistics(**payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"amount": 1},
        {"amount": 1, "comment": "test_comment"},
        {
            "amount": 1,
            "comment": "test_comment",
            "life_time": datetime.datetime.now() + datetime.timedelta(hours=5)
        },
        {
            "amount": 1,
            "comment": "test_comment",
            "life_time": datetime.datetime.now() + datetime.timedelta(hours=5),
            "bill_id": str(uuid.uuid4())
        }
    ])
async def test_create_p2p_bill(api: QiwiWrapper, payload: dict):
    async with api:
        result = await api.create_p2p_bill(**payload)

    assert isinstance(result, types.Bill)
    assert payload["amount"] == result.amount.value


async def test_check_p2p_bill_status(api: QiwiWrapper):
    async with api:
        result = await api.check_p2p_bill_status(
            bill_id="8d517426-920a-4711-86c2-4267784bf901"
        )
    assert isinstance(result, str)


async def test_check_p2p_on_object(api: QiwiWrapper):
    async with api:
        bill = await api.create_p2p_bill(amount=1)
        result = await bill.check()

    assert isinstance(result, bool)


@pytest.mark.parametrize("rows", [5, 10, 50])
async def test_get_bills(api: QiwiWrapper, rows: int):
    async with api:
        result = await api.get_bills(rows=rows)

    assert isinstance(result, list)
    assert all(isinstance(b, types.Bill) for b in result)


async def test_check_restriction(api: QiwiWrapper):
    async with api:
        result = await api.check_restriction()

    assert isinstance(result, list)
    assert all(isinstance(r, types.Restriction) for r in result)


async def test_commission(api: QiwiWrapper):
    async with api:
        result = await api.commission(
            to_account="+380985272064",
            pay_sum=999
        )
    assert isinstance(result, types.Commission)


async def test_get_cross_rates(api: QiwiWrapper):
    async with api:
        result = await api.get_cross_rates()

    assert all(isinstance(r, types.CrossRate) for r in result)


class TestFail:

    @pytest.mark.parametrize("rows_num", [-5, 51, 0])
    async def test_transactions_fail(self, api: QiwiWrapper, rows_num: int):
        async with api:
            with pytest.raises(InvalidData):
                await api.transactions(rows_num=rows_num)

    @pytest.mark.parametrize("start_date,end_date", [
        {
            "start_date": datetime.datetime.now() - datetime.timedelta(
                days=100),
            "end_date": datetime.datetime.now()
        },
        {
            "start_date": datetime.datetime.now() - datetime.timedelta(
                days=80),
            "end_date": "Wrong Parameter"
        }
    ])
    async def test_fetch_statistic_fail(
            self,
            api: QiwiWrapper,
            start_date: Union[datetime.datetime, datetime.timedelta],
            end_date: Union[datetime.datetime, datetime.timedelta]
    ):
        async with api:
            with pytest.raises(ValueError):
                await api.fetch_statistics(
                    start_date=start_date,
                    end_date=end_date
                )
