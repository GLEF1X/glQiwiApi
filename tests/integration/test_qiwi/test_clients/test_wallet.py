import asyncio
import datetime
from typing import Dict, Any, AsyncIterator

import pytest

from glQiwiApi import QiwiWallet
from glQiwiApi.base.types.amount import AmountWithCurrency, CurrencyModel
from glQiwiApi.base.types.arbitrary import File
from glQiwiApi.qiwi.clients.p2p.types import Bill
from glQiwiApi.qiwi.clients.wallet.types import TransactionType, Transaction, Identification, Card, \
    QiwiAccountInfo, Statistic, Balance, Restriction, Commission, CrossRate, WebhookInfo
from tests.settings import QIWI_WALLET_CREDENTIALS

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
def event_loop(request: pytest.FixtureRequest) -> AsyncIterator[asyncio.AbstractEventLoop]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(name="api", scope="module")
async def api_fixture() -> AsyncIterator[QiwiWallet]:
    wallet = QiwiWallet(**QIWI_WALLET_CREDENTIALS)
    yield wallet
    await wallet.close()


async def test_get_balance(api: QiwiWallet) -> None:
    result = await api.get_balance()
    assert isinstance(result, AmountWithCurrency)
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
async def test_transactions(api: QiwiWallet, payload: Dict[str, Any]) -> None:
    async with api:
        result = await api.history(**payload)

    assert all(isinstance(t, Transaction) for t in result)


@pytest.mark.parametrize(
    "payload",
    [{"transaction_id": 21601937643, "transaction_type": TransactionType.OUT}],
)
async def test_transaction_info(api: QiwiWallet, payload: Dict[str, Any]) -> None:
    result = await api.get_transaction_info(**payload)
    assert isinstance(result, Transaction)


async def test_identification(api: QiwiWallet) -> None:
    result = await api.get_identification()
    assert isinstance(result, Identification)


@pytest.mark.parametrize(
    "payload",
    [
        {"transaction_type": TransactionType.OUT, "amount": 1},
        {
            "transaction_type": TransactionType.OUT,
            "amount": 1,
            "sender": "+380985272064",
        },
        {"transaction_type": TransactionType.OUT, "amount": 1, "sender": "+380985272064"},
    ],
)
async def test_check_transaction(api: QiwiWallet, payload: Dict[str, Any]) -> None:
    r = await api.check_transaction(**payload)
    assert r is True


async def test_get_limits(api: QiwiWallet) -> None:
    result = await api.get_limits()
    assert isinstance(result, dict)
    assert all([isinstance(t, list) for t in result.values()])


async def test_get_list_of_cards(api: QiwiWallet) -> None:
    result = await api.get_list_of_cards()
    assert all(isinstance(c, Card) for c in result) is True


async def test_get_receipt(api: QiwiWallet) -> None:
    payload = {"transaction_id": 21601937643, "transaction_type": TransactionType.OUT}
    response = await api.get_receipt(**payload)  # type: ignore
    assert isinstance(response, File) is True


async def test_account_info(api: QiwiWallet) -> None:
    result = await api.get_account_info()
    assert isinstance(result, QiwiAccountInfo) is True


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
async def test_fetch_statistic(api: QiwiWallet, payload: Dict[str, Any]) -> None:
    result = await api.fetch_statistics(**payload)
    assert isinstance(result, Statistic)


async def test_list_of_balances(api: QiwiWallet) -> None:
    balances = await api.list_of_balances()
    assert all(isinstance(b, Balance) for b in balances)


async def test_fail_fetch_statistic(api: QiwiWallet) -> None:
    payload = {
        # Wrong start date
        "start_date": datetime.datetime.now() - datetime.timedelta(days=100),
        "end_date": datetime.datetime.now(),
        "operation": "OUT",
    }
    with pytest.raises(ValueError):
        await api.fetch_statistics(**payload)


@pytest.mark.parametrize("rows", [5, 10, 50])
async def test_get_bills(api: QiwiWallet, rows: int) -> None:
    result = await api.list_of_invoices(rows=rows)
    assert isinstance(result, list)
    assert all(isinstance(b, Bill) for b in result)


async def test_check_restriction(api: QiwiWallet) -> None:
    result = await api.get_restrictions()
    assert isinstance(result, list)
    assert all(isinstance(r, Restriction) for r in result)


@pytest.mark.parametrize(
    "payload",
    [
        {"to_account": "+380985272064", "invoice_amount": 999},
        {"to_account": "4890494756089082", "invoice_amount": 1},
    ],
)
async def test_commission(api: QiwiWallet, payload: Dict[str, Any]) -> None:
    result = await api.predict_commission(**payload)
    assert isinstance(result, Commission)


async def test_get_cross_rates(api: QiwiWallet) -> None:
    result = await api.get_cross_rates()
    assert all(isinstance(r, CrossRate) for r in result)


async def test_register_webhook(api: QiwiWallet) -> None:
    config, key = await api.bind_webhook(url="https://45.147.178.166:80//", delete_old=True)

    assert isinstance(config, WebhookInfo)
    assert isinstance(key, str)


async def test_create_new_balance(api: QiwiWallet) -> None:
    response = await api.create_new_balance(currency_alias="qw_wallet_eur")
    assert isinstance(response, dict)


async def test_available_balances(api: QiwiWallet) -> None:
    balances = await api.available_balances()
    assert all(isinstance(b, Balance) for b in balances)


async def test_set_default_balance(api: QiwiWallet) -> None:
    response = await api.set_default_balance(currency_alias="qw_wallet_rub")
    assert isinstance(response, dict)


class TestFail:
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
            api: QiwiWallet,
            start_date: datetime.datetime,
            end_date: datetime.datetime,
    ) -> None:
        with pytest.raises(ValueError):
            await api.fetch_statistics(start_date=start_date, end_date=end_date)
