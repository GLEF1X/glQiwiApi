import abc
import asyncio
import unittest
from typing import AsyncGenerator, Optional, Dict, Any, Union, List

from aiohttp import ClientSession
from aiohttp.typedefs import LooseCookies

from glQiwiApi.types import ProxyService, Response


class BaseStorage(abc.ABC):
    """
    Абстрактный класс контроллера кэша

    """
    __slots__ = ('tmp_data', '_cache_time')

    @abc.abstractmethod
    def get_current(self, key: str) -> Any:
        raise NotImplementedError

    @abc.abstractmethod
    def clear(self, key: str, force: bool = False) -> Any:
        raise NotImplementedError

    @abc.abstractmethod
    def update_data(
            self,
            result: Any,
            kwargs: Any,
            status_code: Optional[Union[str, int]] = None
    ) -> None:
        raise NotImplementedError

    def validate(self, kwargs: Dict[str, Any]) -> None:
        """ Should validate some data from cache """


class AbstractPaymentWrapper(abc.ABC):
    """
    Abstract class for payment wrappers,
    you can add a new one, using this class, and than,
    just send a pull request to GitHub repository,
    if it will be pretty and simple, our team
    add it to the library in next release

    """

    @abc.abstractmethod
    async def transactions(self, *args, **kwargs) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def transaction_info(self, *args, **kwargs) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_balance(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def account_info(self, *args, **kwargs) -> None:
        raise NotImplementedError


class AioTestCase(unittest.TestCase):
    """ Test case, but redone for asyncio """

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
    """ Abstract class of parser for send request to different API's"""

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
        raise NotImplementedError

    @abc.abstractmethod
    async def fetch(
            self,
            *,
            times: int = 1,
            **kwargs
    ) -> AsyncGenerator[Response, None]:
        """ You can override it, but is must to return an AsyncGenerator """
        raise NotImplementedError

    def raise_exception(
            self,
            status_code: Union[str, int],
            json_info: Optional[Dict[str, Any]] = None,
            message: Optional[str] = None
    ) -> None:
        """Метод для обработки исключений и лучшего логирования"""

    def create_session(self, **kwargs) -> None:
        """ Creating new session if old was close or it's None """
        if self.session is None:
            self.session = ClientSession(**kwargs)
        elif isinstance(self.session, ClientSession):
            if self.session.closed:
                self.session = ClientSession(**kwargs)
