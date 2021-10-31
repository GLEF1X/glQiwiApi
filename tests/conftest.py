from datetime import datetime

import pytest

from glQiwiApi.types import WebHook, Transaction, TransactionStatus, CurrencyAmount
from glQiwiApi.types.qiwi.transaction import Provider, TransactionType

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="credentials", scope="module")
def credentials():
    from .types.dataset import API_DATA

    """ credentials fixture """
    yield API_DATA


@pytest.fixture(name="yoo_credentials")
def credentials_fixture():
    from .types.dataset import YOO_MONEY_DATA

    yield YOO_MONEY_DATA


@pytest.fixture()
def transaction() -> Transaction:
    return Transaction(
        txnId=50,
        personId=3254235,
        date=datetime.now(),
        status=TransactionStatus.SUCCESS,
        statusText="hello",
        trmTxnId="world",
        account="+38908234234",
        sum=CurrencyAmount(amount=999, currency="643"),
        total=CurrencyAmount(amount=999, currency="643"),
        provider=Provider(),
        commission=CurrencyAmount(amount=999, currency="643"),
        currencyRate=643,
        type=TransactionType.OUT,
        comment="my_comment"
    )


@pytest.fixture(name="test_webhook")
def test_webhook_fixture():
    return WebHook.parse_obj(
        {'messageId': 'dc32ba01-1a83-4dc5-82b5-1148f7744ace',
         'hookId': '87995a67-749f-4a23-9629-95dc8fea696f',
         'payment': {'txnId': '22994210671', 'date': '2021-08-24T22:48:03+03:00', 'type': 'OUT',
                     'status': 'SUCCESS',
                     'errorCode': '0', 'personId': 380968317459, 'account': '+380985272064',
                     'comment': '',
                     'provider': 99, 'sum': {'amount': 1, 'currency': 643},
                     'commission': {'amount': 0.02, 'currency': 643},
                     'total': {'amount': 1.02, 'currency': 643},
                     'signFields': 'sum.currency,sum.amount,type,account,txnId'},
         'hash': '1de3c14fbe8687b71b34ee23bd55262167304bb8f7d1bb8adaa5d8b4474fb148',
         'version': '1.0.0', 'test': False}
    )
