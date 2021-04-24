import abc
import asyncio
import unittest
from typing import AsyncGenerator, Optional, Dict, Any, Union, List, Tuple

from aiohttp import ClientSession, web
from aiohttp.typedefs import LooseCookies

from glQiwiApi import types
from glQiwiApi.core.web_hooks.handler import HandlerManager
from glQiwiApi.types import Response


class BaseStorage(abc.ABC):
    """
    Абстрактный класс контроллера кэша

    """

    @abc.abstractmethod
    def get_current(self, key: str) -> Any:
        raise NotImplementedError

    @abc.abstractmethod
    def clear(self, key: str, force: bool = False) -> Any:
        raise NotImplementedError

    def update_data(self, obj_to_cache: Any, key: Any) -> None:
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


class BaseWebHookView(web.View):
    """
    Base webhook view for processing events
    You can make own view and than use it in code,
    just inheriting this base class

    """
    app_key_check_ip: Optional[str] = None
    """app_key_check_ip stores key to a storage"""

    app_key_handler_manager: Optional[str] = None
    """app_key_handler_manager"""

    def _check_ip(self, ip_address: str):
        """_check_ip checks if given IP is in set of allowed ones"""
        raise NotImplementedError

    async def parse_update(self):
        """parse_update method that deals with marshaling json"""
        raise NotImplementedError

    def validate_ip(self):
        """ validating request ip address """
        if self.request.app.get(self.app_key_check_ip):
            ip_addr_data = self.check_ip()
            if not ip_addr_data[1]:
                raise web.HTTPUnauthorized()

    def check_ip(self) -> Union[Tuple[str, bool], Tuple[None, bool]]:
        """ checking ip, using headers or peer_name """
        forwarded_for = self.request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for, self._check_ip(forwarded_for)
        peer_name = self.request.transport.get_extra_info("peername")

        if peer_name is not None:
            host, _ = peer_name
            return host, self._check_ip(host)

        return None, False

    @abc.abstractmethod
    async def post(self) -> None:
        """
        Process POST request with basic IP validation.

        """
        self.validate_ip()

        update = await self.parse_update()

        self._hash_validator(update)

        await self.handler_manager.process_event(update)

    def _hash_validator(self, update: Union[
        types.Notification, types.WebHook
    ]) -> None:
        """ Validating by hash of update """

    @property
    def handler_manager(self) -> "HandlerManager":
        """ Return handler manager """
        return self.request.app.get(
            self.app_key_handler_manager)  # type: ignore
