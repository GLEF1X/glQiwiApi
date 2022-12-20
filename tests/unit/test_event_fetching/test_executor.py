import asyncio
from datetime import datetime
from typing import List, NoReturn, Optional

import async_timeout
import pytest

from glQiwiApi import QiwiWallet
from glQiwiApi.core.event_fetching.dispatcher import QiwiDispatcher
from glQiwiApi.core.event_fetching.executor import (
    HandlerContext,
    ExecutorEvent,
    start_non_blocking_qiwi_api_polling,
)
from glQiwiApi.qiwi.clients.wallet.types import History, Source, Transaction, TransactionType
from glQiwiApi.yoo_money.methods.operation_history import MAX_HISTORY_LIMIT


class TestExecutorEvent:
    async def test_fire(self):
        context = HandlerContext({'api_key': 'fake_api_key'})

        async def init_event(ctx: HandlerContext) -> NoReturn:
            assert ctx == context
            raise RuntimeError()

        event = ExecutorEvent(context, init_handlers=[init_event])
        event += init_event
        event -= init_event

        with pytest.raises(RuntimeError):
            await event.fire()

    async def test_fire_sync_handlers(self):
        context = HandlerContext({'api_key': 'fake_api_key'})

        event = ExecutorEvent(context)

        def on_event(ctx: HandlerContext) -> NoReturn:
            assert ctx == context
            raise RuntimeError()

        event += on_event

        with pytest.raises(RuntimeError):
            await event.fire()


class WalletStub(QiwiWallet):
    def __init__(self, fake_transaction: Transaction, api_access_token: str = ''):
        super().__init__(api_access_token)
        self._fake_transaction = fake_transaction

    async def history(
        self,
        rows: int = MAX_HISTORY_LIMIT,
        transaction_type: TransactionType = TransactionType.ALL,
        sources: Optional[List[Source]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        next_txn_date: Optional[datetime] = None,
        next_txn_id: Optional[int] = None,
    ) -> History:
        return History(data=[self._fake_transaction])


async def test_start_non_blocking_qiwi_api_polling(transaction: Transaction) -> None:
    c = HandlerContext({'api_key': 'my_api_key'})
    wallet = WalletStub(transaction)
    dp = QiwiDispatcher()

    handled_transaction_event = asyncio.Event()
    handle_on_startup = asyncio.Event()

    @dp.transaction_handler()
    async def handle_transaction(txn: Transaction, ctx: HandlerContext):
        assert ctx['api_key'] == 'my_api_key'
        assert ctx.wallet == wallet
        handled_transaction_event.set()

    async def on_startup(ctx: HandlerContext):
        assert ctx['api_key'] == 'my_api_key'
        assert ctx.wallet == wallet
        handle_on_startup.set()

    async with async_timeout.timeout(5):
        await start_non_blocking_qiwi_api_polling(wallet, dp, context=c, on_startup=on_startup)
        await handle_on_startup.wait()
        await handled_transaction_event.wait()

    assert handled_transaction_event.is_set()
    assert handle_on_startup.is_set()
