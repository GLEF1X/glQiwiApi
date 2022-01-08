import asyncio
from datetime import datetime
from typing import List, Optional

import pytest
import timeout_decorator

from glQiwiApi import QiwiWallet
from glQiwiApi.core.dispatcher.implementation import Dispatcher, Event
from glQiwiApi.qiwi.types import Transaction, TransactionType, Source
from glQiwiApi.utils import executor

pytestmark = pytest.mark.asyncio


class StubDispatcher(Dispatcher):
    def __init__(self, fake_event: Event) -> None:
        super().__init__()
        self._fake_event = fake_event

    async def process_event(self, event: Event = None) -> None:
        await super().process_event(self._fake_event)


class StubQiwiWrapper(QiwiWallet):
    def __init__(self, fake_event: Transaction, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fake_transaction = fake_event
        self._dispatcher = StubDispatcher(fake_event)

    def __new__(cls, *args, **kwargs):
        return object().__new__(cls)

    async def history(
        self,
        rows: int = 50,
        operation: TransactionType = TransactionType.ALL,
        sources: Optional[List[Source]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Transaction]:
        return [self._fake_transaction]


@pytest.fixture(name="api")
async def api_fixture(transaction: Transaction):
    """Api fixture"""
    _wrapper = StubQiwiWrapper(fake_event=transaction, api_access_token="hello")
    yield _wrapper
    await _wrapper.close()


async def _on_startup_callback(api: QiwiWallet):
    await asyncio.sleep(1)
    await api.dispatcher.process_event()  # type: ignore  # noqa


class TestPolling:
    @timeout_decorator.timeout(2)
    def _start_polling(self, api: QiwiWallet):

        self._handled_first = asyncio.Event()
        self._handled_second = asyncio.Event()
        self.on_shutdown_event = asyncio.Event()

        # Also, without decorators, you can do like this
        # api.dispatcher.register_transaction_handler(my_handler)
        @api.transaction_handler()
        async def my_first_handler(event: Transaction):
            self._handled_first.set()
            assert isinstance(event, Transaction)

        @api.transaction_handler()
        async def my_second_handler(event: Transaction):
            self._handled_second.set()
            assert isinstance(event, Transaction)

        executor.start_polling(api, on_startup=_on_startup_callback)

    @pytest.mark.skipif("sys.platform in ['cygwin', 'msys', 'win32']")
    def test_as_if_used_by_a_user(self, api: QiwiWallet):
        try:
            self._start_polling(api)
        except timeout_decorator.TimeoutError:
            assert self._handled_first.is_set()
            assert not self._handled_second.is_set()
        finally:
            self._handled_first.clear()
            self._handled_second.clear()
