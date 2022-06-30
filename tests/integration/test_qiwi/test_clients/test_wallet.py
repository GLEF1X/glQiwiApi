import asyncio
import contextlib
import datetime
from typing import Any, AsyncIterator, Dict

import pytest

from glQiwiApi import APIResponsesCacheInvalidationStrategy, InMemoryCacheStorage, QiwiWallet
from glQiwiApi.core import RequestService
from glQiwiApi.core.request_service import RequestServiceCacheDecorator
from glQiwiApi.core.session import AiohttpSessionHolder
from glQiwiApi.ext.webhook_url import WebhookURL
from glQiwiApi.qiwi.clients.p2p.types import Bill
from glQiwiApi.qiwi.clients.wallet.types import (
    Balance,
    Card,
    Commission,
    CrossRate,
    Identification,
    Restriction,
    Source,
    Statistic,
    Transaction,
    TransactionType,
    UserProfile,
    WebhookInfo,
)
from glQiwiApi.qiwi.clients.wallet.types.balance import AvailableBalance
from glQiwiApi.qiwi.clients.wallet.types.nickname import NickName
from glQiwiApi.qiwi.exceptions import MobileOperatorCannotBeDeterminedError, ObjectNotFoundError
from glQiwiApi.types.amount import Amount, CurrencyModel
from glQiwiApi.types.arbitrary import File
from tests.settings import QIWI_WALLET_CREDENTIALS

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope='module')
def event_loop(request: pytest.FixtureRequest) -> AsyncIterator[asyncio.AbstractEventLoop]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(name='api', scope='module')
async def api_fixture() -> AsyncIterator[QiwiWallet]:
    async with QiwiWallet(**QIWI_WALLET_CREDENTIALS) as wallet:
        yield wallet


async def test_get_balance(api: QiwiWallet) -> None:
    result = await api.get_balance()
    assert isinstance(result, Amount)
    assert isinstance(result.currency, CurrencyModel)


def test_create_request_service() -> None:
    cache_storage = InMemoryCacheStorage(
        invalidate_strategy=APIResponsesCacheInvalidationStrategy()
    )

    def create_request_service_with_cache(w: QiwiWallet):
        return RequestServiceCacheDecorator(
            RequestService(
                session_holder=AiohttpSessionHolder(
                    headers={
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'Authorization': f'Bearer {w._api_access_token}',
                        'Host': 'edge.qiwi.com',
                    },
                )
            ),
            cache_storage=cache_storage,
        )

    wallet = QiwiWallet(
        **QIWI_WALLET_CREDENTIALS, request_service_factory=create_request_service_with_cache
    )
    wallet.create_request_service()

    assert wallet._request_service._cache is cache_storage


@pytest.mark.parametrize(
    'payload',
    [
        {'rows': 50},
        {'rows': 50, 'transaction_type': TransactionType.IN},
        {
            'rows': 50,
            'transaction_type': TransactionType.IN,
            'start_date': datetime.datetime.now() - datetime.timedelta(days=50),
            'end_date': datetime.datetime.now(),
        },
        {
            'rows': 50,
            'transaction_type': TransactionType.IN,
            'start_date': datetime.datetime.now() - datetime.timedelta(days=50),
            'end_date': datetime.datetime.now(),
            'sources': [Source.MK, Source.RUB],
        },
    ],
)
async def test_history(api: QiwiWallet, payload: Dict[str, Any]) -> None:
    async with api:
        result = await api.history(**payload)

    assert all(isinstance(t, Transaction) for t in result)


@pytest.mark.parametrize(
    'payload',
    [{'transaction_id': 21601937643, 'transaction_type': TransactionType.OUT}],
)
async def test_transaction_info(api: QiwiWallet, payload: Dict[str, Any]) -> None:
    result = await api.get_transaction_info(**payload)
    assert isinstance(result, Transaction)


async def test_identification(api: QiwiWallet) -> None:
    result = await api.get_identification()
    assert isinstance(result, Identification)


async def test_check_whether_transaction_exists_using_check_fn_with_id(api: QiwiWallet) -> None:
    transactions = await api.history()

    test_transaction = transactions[-1]
    r = await api.check_whether_transaction_exists(check_fn=lambda t: t.id == test_transaction.id)
    assert r is True


async def test_get_limits(api: QiwiWallet) -> None:
    result = await api.get_limits()
    assert isinstance(result, dict)
    assert all([isinstance(t, list) for t in result.values()])


async def test_get_list_of_cards(api: QiwiWallet) -> None:
    result = await api.get_list_of_cards()
    assert all(isinstance(c, Card) for c in result) is True


async def test_get_receipt(api: QiwiWallet) -> None:
    payload = {'transaction_id': 21601937643, 'transaction_type': TransactionType.OUT}
    response = await api.get_receipt(**payload)  # type: ignore
    assert isinstance(response, File) is True


async def test_get_profile(api: QiwiWallet) -> None:
    result = await api.get_profile()
    assert isinstance(result, UserProfile) is True


@pytest.mark.parametrize(
    'payload',
    [
        {
            'start_date': datetime.datetime.now() - datetime.timedelta(days=50),
            'end_date': datetime.datetime.now(),
        },
        {
            'start_date': datetime.datetime.now() - datetime.timedelta(days=50),
            'end_date': datetime.datetime.now(),
            'operation': TransactionType.IN,
        },
        {
            'start_date': datetime.datetime.now() - datetime.timedelta(days=50),
            'end_date': datetime.datetime.now(),
            'operation': TransactionType.OUT,
        },
        {
            'start_date': datetime.datetime.now() - datetime.timedelta(days=50),
            'end_date': datetime.datetime.now(),
            'operation': TransactionType.ALL,
        },
        {
            'start_date': datetime.datetime.now() - datetime.timedelta(days=50),
            'end_date': datetime.datetime.now(),
            'operation': TransactionType.ALL,
            'sources': ['QW_RUB'],
        },
        {
            'start_date': datetime.datetime.now() - datetime.timedelta(days=50),
            'end_date': datetime.datetime.now(),
            'operation': TransactionType.ALL,
            'sources': ['QW_RUB', 'QW_EUR', 'QW_USD'],
        },
    ],
)
async def test_fetch_statistic(api: QiwiWallet, payload: Dict[str, Any]) -> None:
    result = await api.fetch_statistics(**payload)
    assert isinstance(result, Statistic)


async def test_list_of_balances(api: QiwiWallet) -> None:
    balances = await api.get_list_of_balances()
    assert all(isinstance(b, Balance) for b in balances)


async def test_fail_fetch_statistic(api: QiwiWallet) -> None:
    payload = {
        # Wrong start date
        'start_date': datetime.datetime.now() - datetime.timedelta(days=100),
        'end_date': datetime.datetime.now(),
        'operation': 'OUT',
    }
    with pytest.raises(ValueError):
        await api.fetch_statistics(**payload)


async def test_get_nickname(api: QiwiWallet) -> None:
    assert isinstance(await api.get_nickname(), NickName)


@pytest.mark.parametrize('rows', [5, 10, 50])
async def test_get_bills(api: QiwiWallet, rows: int) -> None:
    result = await api.list_of_invoices(rows=rows)
    assert isinstance(result, list)
    assert all(isinstance(b, Bill) for b in result)


async def test_check_restriction(api: QiwiWallet) -> None:
    result = await api.get_restrictions()
    assert isinstance(result, list)
    assert all(isinstance(r, Restriction) for r in result)


@pytest.mark.parametrize(
    'payload',
    [
        {'to_account': '+380985272064', 'invoice_amount': 999},
        {'to_account': '4890494756089082', 'invoice_amount': 1},
    ],
)
async def test_commission(api: QiwiWallet, payload: Dict[str, Any]) -> None:
    result = await api.predict_commission(**payload)
    assert isinstance(result, Commission)


async def test_get_cross_rates(api: QiwiWallet) -> None:
    result = await api.get_cross_rates()
    assert all(isinstance(r, CrossRate) for r in result)


@pytest.mark.skip
async def test_create_new_balance(api: QiwiWallet) -> None:
    response = await api.create_new_balance(currency_alias='qw_wallet_usd')
    assert isinstance(response, dict)


async def test_get_available_balances(api: QiwiWallet) -> None:
    balances = await api.get_available_balances()
    assert all(isinstance(b, AvailableBalance) for b in balances)


@pytest.mark.skip
async def test_set_default_balance(api: QiwiWallet) -> None:
    response = await api.set_default_balance(account_alias='qw_wallet_rub')
    assert isinstance(response, dict)


class TestFail:
    @pytest.mark.parametrize(
        'start_date,end_date',
        [
            {
                'start_date': datetime.datetime.now() - datetime.timedelta(days=100),
                'end_date': datetime.datetime.now(),
            },
            {
                'start_date': datetime.datetime.now() - datetime.timedelta(days=80),
                'end_date': 'Wrong Parameter',
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


def test_raise_runtimeError_if_phone_number_is_empty() -> None:
    wallet = QiwiWallet(api_access_token='hello world')
    with pytest.raises(RuntimeError):
        wallet.phone_number_without_plus_sign


async def test_detect_mobile_number_fail_if_phone_number_is_ukrainian(api: QiwiWallet):
    with pytest.raises(MobileOperatorCannotBeDeterminedError):
        await api.detect_mobile_operator('+380985272064')


class TestWebhooksAPI:
    @pytest.mark.parametrize(
        'payload',
        [
            {'url': 'https://45.147.178.166:80/webhooks/qiwi'},
            {
                'url': WebhookURL.create(
                    host='45.147.178.166', port=80, webhook_path='/webhook/qiwi', https=True
                )
            },
            {'url': 'https://45.147.178.166:80/webhooks/qiwi', 'send_test_notification': True},
            {
                'url': WebhookURL.create(
                    host='45.147.178.166', port=80, webhook_path='/webhook/qiwi', https=True
                ),
                'send_test_notification': True,
            },
            {'url': 'https://45.147.178.166:80/webhooks/qiwi', 'send_test_notification': True},
        ],
    )
    async def test_bind_webhook(self, api: QiwiWallet, payload: Dict[str, Any]) -> None:
        await api.bind_webhook(**payload, delete_old=True)

    async def test_register_webhook(self, api: QiwiWallet) -> None:
        config, key = await api.bind_webhook(url='https://45.147.178.166:80//', delete_old=True)

        assert isinstance(config, WebhookInfo)
        assert isinstance(key, str)

    async def test_delete_current_webhook(self, api: QiwiWallet) -> None:
        config, key = await api.bind_webhook(url='https://45.147.178.166:80//', delete_old=True)
        await api.delete_current_webhook()

        with pytest.raises(ObjectNotFoundError):
            await api.get_current_webhook()

    async def test_generate_new_webhook_secret_key(self, api: QiwiWallet) -> None:
        with contextlib.suppress(ObjectNotFoundError):
            await api.delete_current_webhook()

        webhook = await api.register_webhook(url='https://45.147.178.166:80//')

        assert isinstance(await api.generate_new_webhook_secret(webhook.id), str) is True
