import asyncio
import datetime
import uuid

import pytest

from glQiwiApi import QiwiWrapper
from glQiwiApi import types, InvalidPayload
from glQiwiApi.types import TransactionType
from glQiwiApi.types.arbitrary.file import File

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(name="api", scope="module")
async def api_fixture(credentials: dict):
    """Api fixture"""
    _wrapper = QiwiWrapper(**credentials)
    yield _wrapper
    await _wrapper.close()


async def test_get_balance(api: QiwiWrapper):
    from glQiwiApi.types.amount import CurrencyModel
    result = await api.get_balance()
    assert isinstance(result, types.CurrencyAmount)
    assert isinstance(result.currency, CurrencyModel)


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
async def test_transactions(api: QiwiWrapper, payload: dict):
    async with api:
        result = await api.transactions(**payload)

    assert all(isinstance(t, types.Transaction) for t in result)


@pytest.mark.parametrize(
    "payload",
    [{"transaction_id": 21601937643, "transaction_type": TransactionType.OUT}],
)
async def test_transaction_info(api: QiwiWrapper, payload: dict):
    result = await api.transaction_info(**payload)
    assert isinstance(result, types.Transaction)


async def test_identification(api: QiwiWrapper):
    result = await api.get_identification()
    assert isinstance(result, types.Identification)


@pytest.mark.parametrize(
    "payload",
    [
        {"transaction_type": TransactionType.OUT, "amount": 1},
        {
            "transaction_type": TransactionType.OUT,
            "amount": 1,
            "sender": "+380985272064",
        },
        {
            "transaction_type": TransactionType.OUT,
            "amount": 1,
            "sender": "+380985272064"
        },
    ],
)
async def test_check_transaction(api: QiwiWrapper, payload: dict):
    r = await api.check_transaction(**payload)
    assert r is True


async def test_get_limits(api: QiwiWrapper):
    result = await api.get_limits()
    assert isinstance(result, dict)
    assert all([isinstance(t, list) for t in result.values()])


async def test_get_list_of_cards(api: QiwiWrapper):
    result = await api.get_list_of_cards()
    assert all(isinstance(c, types.Card) for c in result) is True


async def test_get_receipt(api: QiwiWrapper):
    payload = {"transaction_id": 21601937643, "transaction_type": TransactionType.OUT}
    response = await api.get_receipt(**payload)  # type: ignore
    assert isinstance(response, File) is True


async def test_account_info(api: QiwiWrapper):
    result = await api.get_account_info()
    assert isinstance(result, types.QiwiAccountInfo) is True


@pytest.mark.parametrize(
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
async def test_fetch_statistic(api: QiwiWrapper, payload: dict):
    result = await api.fetch_statistics(**payload)
    assert isinstance(result, types.Statistic)


async def test_list_of_balances(api: QiwiWrapper):
    balances = await api.list_of_balances()
    assert all(isinstance(b, types.Account) for b in balances)


async def test_fail_fetch_statistic(api: QiwiWrapper):
    payload = {
        # Wrong start date
        "start_date": datetime.datetime.now() - datetime.timedelta(days=100),
        "end_date": datetime.datetime.now(),
        "operation": "OUT",
    }
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
async def test_create_p2p_bill(api: QiwiWrapper, payload: dict):
    result = await api.create_p2p_bill(**payload)
    assert isinstance(result, types.Bill)
    assert payload["amount"] == result.amount.value


async def test_check_p2p_bill_status(api: QiwiWrapper):
    test_bill = await api.create_p2p_bill(amount=1)
    result = await api.check_p2p_bill_status(bill_id=test_bill.bill_id)
    assert isinstance(result, str)


async def test_check_p2p_on_object(api: QiwiWrapper):
    api.set_current(api)

    bill = await api.create_p2p_bill(amount=1)
    assert isinstance(bill, types.Bill)
    result = await bill.check()

    assert isinstance(result, bool)


@pytest.mark.parametrize("rows", [5, 10, 50])
async def test_get_bills(api: QiwiWrapper, rows: int):
    result = await api.retrieve_bills(rows=rows)
    assert isinstance(result, list)
    assert all(isinstance(b, types.Bill) for b in result)


async def test_check_restriction(api: QiwiWrapper):
    result = await api.get_restriction()
    assert isinstance(result, list)
    assert all(isinstance(r, types.Restriction) for r in result)


@pytest.mark.parametrize(
    "payload",
    [
        {"to_account": "+380985272064", "pay_sum": 999},
        {"to_account": "4890494756089082", "pay_sum": 1},
    ],
)
async def test_commission(api: QiwiWrapper, payload: dict):
    result = await api.predict_commission(**payload)
    assert isinstance(result, types.Commission)


async def test_get_cross_rates(api: QiwiWrapper):
    result = await api.get_cross_rates()
    assert all(isinstance(r, types.CrossRate) for r in result)


async def test_register_webhook(api: QiwiWrapper):
    config, key = await api.bind_webhook(
        url="https://45.147.178.166:80//", delete_old=True
    )

    assert isinstance(config, types.WebHookConfig)
    assert isinstance(key, str)


async def test_create_new_balance(api: QiwiWrapper):
    response = await api.create_new_balance(currency_alias="qw_wallet_eur")
    assert isinstance(response, dict)


async def test_available_balances(api: QiwiWrapper):
    balances = await api.available_balances()
    assert all(isinstance(b, types.Balance) for b in balances)


async def test_set_default_balance(api: QiwiWrapper):
    response = await api.set_default_balance(currency_alias="qw_wallet_rub")
    assert isinstance(response, dict)


async def test_reject_p2p_bill(api: QiwiWrapper):
    b = await api.create_p2p_bill(amount=1)
    rejected_bill = await api.reject_p2p_bill(b.bill_id)
    assert isinstance(rejected_bill, types.Bill)


class TestFail:
    @pytest.mark.parametrize("rows", [-5, 51, 0])
    async def test_transactions_fail(self, api: QiwiWrapper, rows: int):
        with pytest.raises(InvalidPayload):
            await api.transactions(rows=rows)

    @pytest.mark.parametrize("rows", [-5, 51, 0])
    async def test_retrieve_bills_fail_if_rows_num_not_in_normal_boundaries(self, api: QiwiWrapper,
                                                                            rows: int):
        with pytest.raises(InvalidPayload):
            await api.retrieve_bills(rows=rows)

    @pytest.mark.parametrize(
        "start_date,end_date",
        [
            {
                "start_date": datetime.datetime.now() - datetime.timedelta(days=100),
                "end_date": datetime.datetime.now(),
            },
            {
                "start_date": datetime.datetime.now() - datetime.timedelta(days=80),
                "end_date": "Wrong Parameter",
            },
        ],
    )
    async def test_fetch_statistic_fail(
            self,
            api: QiwiWrapper,
            start_date: datetime.datetime,
            end_date: datetime.datetime,
    ):
        with pytest.raises(ValueError):
            await api.fetch_statistics(start_date=start_date, end_date=end_date)


class TestDeprecated:
    async def test_identification_async_property_warns_deprecated(self, api: QiwiWrapper):
        with pytest.deprecated_call():
            await api.identification

    async def test_get_bills_warns_deprecated(self, api: QiwiWrapper):
        with pytest.deprecated_call():
            await api.get_bills(rows_num=50)
