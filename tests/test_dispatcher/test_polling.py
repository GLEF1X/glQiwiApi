import asyncio
from datetime import datetime

import pytest
import timeout_decorator
from _pytest.fixtures import SubRequest

from glQiwiApi import QiwiWrapper
from glQiwiApi import types
from glQiwiApi.types import Transaction, Sum
from glQiwiApi.types.qiwi_types.transaction import Provider

pytestmark = pytest.mark.asyncio

txn = Transaction(txnId=50, personId=3254235, date=datetime.now(),
                  status="OUT", statusText="hello",
                  trmTxnId="world", account="+38908234234",
                  sum=Sum(amount=999, currency=643),
                  total=Sum(amount=999, currency=643),
                  provider=Provider(),
                  commission=Sum(amount=999, currency=643),
                  currencyRate=643, type="OUT")


@pytest.fixture(name='api')
async def api_fixture(credentials: dict, request: SubRequest, capsys):
    """ Api fixture """
    _wrapper = QiwiWrapper(**credentials)
    yield _wrapper
    await _wrapper.close()


async def _on_startup_callback(api: QiwiWrapper):
    await asyncio.sleep(1)
    await api.dispatcher.process_event(txn)


class TestPolling:

    @timeout_decorator.timeout(5)
    def _start_polling(self, api: QiwiWrapper):
        from glQiwiApi.utils import executor

        self._handled = False

        # Also, without decorators, you can do like this
        # api.dispatcher.register_transaction_handler(my_handler)
        @api.transaction_handler()
        async def my_handler(event: types.Transaction):
            self._handled = True
            assert isinstance(event, types.Transaction)

        executor.start_polling(api, on_startup=_on_startup_callback)

    def test_polling(self, api: QiwiWrapper):
        try:
            self._start_polling(api)
        except timeout_decorator.TimeoutError:
            assert self._handled is True
