import asyncio
from datetime import datetime
from typing import Optional, List

import pytest
import timeout_decorator

from glQiwiApi import QiwiWrapper
from glQiwiApi import types
from glQiwiApi.types import Transaction, Sum
from glQiwiApi.types.qiwi_types.transaction import Provider
from tests.types.dataset import WRONG_API_DATA

txn = Transaction(
    txnId=50,
    personId=3254235,
    date=datetime.now(),
    status="OUT",
    statusText="hello",
    trmTxnId="world",
    account="+38908234234",
    sum=Sum(amount=999, currency=643),
    total=Sum(amount=999, currency=643),
    provider=Provider(),
    commission=Sum(amount=999, currency=643),
    currencyRate=643,
    type=types.TransactionType.OUT,
)


class StubQiwiWrapper(QiwiWrapper):
    def __new__(cls, *args, **kwargs):
        return object().__new__(cls)

    async def transactions(
        self,
        rows: int = 50,
        operation: str = "ALL",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Transaction]:
        return [txn]


@pytest.fixture(name="api")
async def api_fixture():
    """Api fixture"""
    _wrapper = StubQiwiWrapper(WRONG_API_DATA)
    yield _wrapper
    await _wrapper.close()


async def _on_startup_callback(api: QiwiWrapper):
    await asyncio.sleep(1)
    await api.dispatcher.process_event(txn)


class TestPolling:
    @pytest.mark.asyncio
    @timeout_decorator.timeout(2)
    def _start_polling(self, api: QiwiWrapper):
        from glQiwiApi.utils import executor

        self._handled_first = asyncio.Event()
        self._handled_second = asyncio.Event()
        self.on_shutdown_event = asyncio.Event()

        # Also, without decorators, you can do like this
        # api.dispatcher.register_transaction_handler(my_handler)
        @api.transaction_handler()
        async def my_first_handler(event: types.Transaction):
            self._handled_first.set()
            assert isinstance(event, types.Transaction)

        @api.transaction_handler()
        async def my_second_handler(event: types.Transaction):
            self._handled_second.set()
            assert isinstance(event, types.Transaction)

        executor.start_polling(api, on_startup=_on_startup_callback)

    @pytest.mark.skipif("sys.platform in ['cygwin', 'msys', 'win32']")
    def test_polling(self, api: QiwiWrapper):
        try:
            self._start_polling(api)
        except timeout_decorator.TimeoutError:
            assert self._handled_first.is_set()
            assert not self._handled_second.is_set()
        finally:
            self._handled_first.clear()
            self._handled_second.clear()
