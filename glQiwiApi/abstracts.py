import abc
import asyncio
import unittest
from typing import AsyncGenerator, Optional, Dict, Any, Union, List

from aiohttp import ClientSession
from aiohttp.typedefs import LooseCookies

from glQiwiApi.types import ProxyService, Response


class AbstractCacheController(abc.ABC):
    """
    Абстрактный класс контроллера кэша

    """
    __slots__ = ('tmp_data', '_cache_time')

    @abc.abstractmethod
    def get_current(self, key: str) -> Any:
        raise NotImplementedError()

    @abc.abstractmethod
    def clear(self, key: str, force: bool = False) -> Any:
        raise NotImplementedError()

    @abc.abstractmethod
    def update_data(
            self,
            result: Any,
            kwargs: Any,
            status_code: Union[str, int]
    ) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def validate(self, kwargs: Dict[str, Any]) -> bool:
        raise NotImplementedError()


class AbstractPaymentWrapper(abc.ABC):
    @abc.abstractmethod
    async def transactions(self, *args, **kwargs) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def transaction_info(self, *args, **kwargs) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def get_balance(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def account_info(self, *args, **kwargs) -> None:
        raise NotImplementedError()


class AioTestCase(unittest.TestCase):

    # noinspection PyPep8Naming
    def __init__(self, methodName='runTest', loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self._function_cache = {}
        super(AioTestCase, self).__init__(methodName=methodName)

    def coroutine_function_decorator(self, func):
        def wrapper(*args, **kw):
            return self.loop.run_until_complete(func(*args, **kw))

        return wrapper

    def __getattribute__(self, item):
        attr = object.__getattribute__(self, item)
        if asyncio.iscoroutinefunction(attr):
            if item not in self._function_cache:
                self._function_cache[
                    item
                ] = self.coroutine_function_decorator(attr)
            return self._function_cache[item]
        return attr


class AbstractParser(abc.ABC):

    def __init__(self):
        self.session: Optional[ClientSession] = None

    @abc.abstractmethod
    async def _request(
            self,
            url: Optional[str],
            get_json: bool,
            method: str,
            set_timeout: bool,
            cookies: Optional[LooseCookies],
            json: Optional[dict],
            skip_exceptions: bool,
            proxy: Optional[ProxyService],
            data: Optional[Dict[str, Union[
                str, int, List[
                    Union[str, int]
                ]]]
            ],
            headers: Optional[Dict[str, Union[str, int]]],
            params: Optional[
                Dict[str, Union[str, int, List[
                    Union[str, int]
                ]]]
            ]) -> Response:
        raise NotImplementedError()

    @abc.abstractmethod
    async def fetch(
            self,
            *,
            times: int = 1,
            **kwargs
    ) -> AsyncGenerator[Response, None]:
        raise NotImplementedError()

    def raise_exception(
            self,
            status_code: Union[str, int],
            json_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """Метод для обработки исключений и лучшего логирования"""

    def create_session(self, **kwargs) -> None:
        if self.session is None:
            self.session = ClientSession(**kwargs)
        elif isinstance(self.session, ClientSession):
            if self.session.closed:
                self.session = ClientSession(**kwargs)
