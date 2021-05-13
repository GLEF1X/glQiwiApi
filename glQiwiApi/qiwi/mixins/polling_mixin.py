import asyncio
import datetime
from typing import Any, Union, Optional, List, \
    Tuple, Callable

from aiohttp import ClientTimeout

from glQiwiApi.types.qiwi_types.transaction import Transaction
from glQiwiApi.utils import basics as api_helper
from glQiwiApi.utils.exceptions import NoUpdatesToExecute

DEFAULT_TIMEOUT = 20.0  # timeout in seconds


def _get_last_payment(
        history: List[Transaction]
) -> Tuple[Optional[Transaction], Optional[int]]:
    """
    Function, which gets last payment and his id of history

    :param history:
    """
    last_payment = history[0]
    last_payment_id = last_payment.transaction_id
    return last_payment, last_payment_id


def _setup_callbacks(
        dispatcher,
        on_startup: Optional[Callable] = None,
        on_shutdown: Optional[Callable] = None
):
    """
    Function, which setup callbacks and set it to dispatcher object

    :param on_startup:
    :param on_shutdown:
    """
    if on_startup is not None:
        dispatcher["on_startup"] = on_startup
    if on_shutdown is not None:
        dispatcher["on_shutdown"] = on_shutdown


def parse_timeout(
        timeout: Union[float, int, ClientTimeout]
) -> Optional[float]:
    """
    Parse timeout

    :param timeout:
    """
    if isinstance(timeout, float):
        return timeout
    elif isinstance(timeout, int):
        return float(timeout)
    elif isinstance(timeout, ClientTimeout):
        return timeout.total
    else:
        raise ValueError("Timeout must be float, int or ClientTimeout. You "
                         f"passed {type(timeout)}")


class HistoryPollingMixin:
    """ Mixin, which provides polling """
    _requests: Any  # type: ignore

    def __init__(self, dispatcher: Any) -> None:
        self.dispatcher = dispatcher

    async def __parse_history_and_process_events(
            self,
            history: List[Transaction],
            last_payment_id: int
    ):
        """
        Processing events and send callbacks to handlers

        :param history: [list] transactions list
        :param last_payment_id: id of last payment in history
        """
        history_iterator = iter(history[::-1])

        while self.dispatcher.offset < last_payment_id:
            try:
                payment = next(history_iterator)
                await self.dispatcher.process_event(payment)
            except StopIteration:  # handle exhausted iterator
                break

            self.dispatcher.offset = payment.transaction_id
            self.dispatcher.offset_start_date = self.dispatcher.offset_end_date

    async def __pre_process(
            self,
            get_updates_from: Optional[datetime.datetime]
    ):
        """
        Pre process method, which set start date and end date of polling
        :param get_updates_from: date from which will be polling
        """
        try:
            current_time = datetime.datetime.now()
            assert isinstance(get_updates_from, datetime.datetime)
            assert (
                           current_time - get_updates_from
                   ).total_seconds() > 0
        except AssertionError as ex:
            raise ValueError(
                "Invalid value of get_updates_from, it must "
                "be instance of datetime and no more than  the current time"
            ) from ex

        self.dispatcher.offset_end_date = current_time

        if self.dispatcher.offset_start_date is None:
            self.dispatcher.offset_start_date = get_updates_from

    async def _get_history(self) -> List[Transaction]:
        """
        Get history by call 'transactions' method from QiwiWrapper.
        If history is empty or not all transactions not isinstance
         class Transaction - raise exception

        """
        history = await self.dispatcher.client.transactions(
            end_date=self.dispatcher.offset_end_date,
            start_date=self.dispatcher.offset_start_date
        )

        if not history or not all(
                isinstance(txn, Transaction) for txn in history):
            raise NoUpdatesToExecute()

        return history

    async def _pool_process(
            self,
            get_updates_from: Optional[datetime.datetime]
    ):
        """
        Method, which manage pool process

        :param get_updates_from: date from which will be polling
        """
        await self.__pre_process(get_updates_from)
        try:
            history = await self._get_history()
        except NoUpdatesToExecute:
            return

        last_payment = history[0]
        last_txn_id = last_payment.transaction_id

        if self.dispatcher.offset is None:
            first_payment = history[-1]
            self.dispatcher.offset = first_payment.transaction_id - 1

        await self.__parse_history_and_process_events(
            history=history,
            last_payment_id=last_txn_id
        )

    async def __start_polling(self, **kwargs):
        """
        Blocking method, which start polling process

        :param kwargs:
        """
        self.dispatcher._polling = True
        self.dispatcher.request_timeout = parse_timeout(kwargs.pop("timeout"))
        while self.dispatcher._polling:
            await self._pool_process(**kwargs)
            await asyncio.sleep(self.dispatcher.request_timeout)

    def __on_shutdown(self, loop: asyncio.AbstractEventLoop):
        """
        On shutdown we gracefully cancel all tasks, close event loop
        and call __aexit__ method to close aiohttp session
        """
        loop.run_until_complete(self.dispatcher.goodbye())
        api_helper.sync(self.__aexit__, None, None, None)
        api_helper.safe_cancel(loop)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрываем сессию и очищаем кэш при выходе"""
        if self._requests.session:
            await self._requests.session.close()
            self._requests.clear_cache()

    def start_polling(
            self,
            get_updates_from: datetime.datetime = datetime.datetime.now(),
            timeout: Union[float, int, ClientTimeout] = DEFAULT_TIMEOUT,
            on_startup: Optional[Callable] = None,
            on_shutdown: Optional[Callable] = None
    ):
        """
        Start long-polling mode

        :param get_updates_from: date from which will be polling,
         if it's None, polling will skip all updates
        :param timeout: timeout of polling in seconds, if the timeout is less,
         the API can throw an exception
        :param on_startup: function or coroutine,
         which will be executed on startup
        :param on_shutdown: function or coroutine,
         which will be executed on shutdown
         """
        self.dispatcher.logger.info("Start polling!")
        loop = api_helper.take_event_loop()
        _setup_callbacks(self.dispatcher, on_startup, on_shutdown)
        try:
            loop.run_until_complete(self.dispatcher.welcome())
            loop.create_task(self.__start_polling(
                get_updates_from=get_updates_from,
                timeout=timeout
            ))
            api_helper.run_forever_safe(loop=loop)
        except (SystemExit, KeyboardInterrupt):
            pass
        finally:
            self.__on_shutdown(loop)
