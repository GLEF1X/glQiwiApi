from __future__ import annotations

import abc
import asyncio
import typing
import unittest
from types import TracebackType
from typing import AsyncGenerator, Optional, Dict, Any, Union, List, Tuple, Type

from aiohttp import web
from aiohttp.typedefs import LooseCookies

from glQiwiApi.core.web_hooks.dispatcher import Dispatcher
from glQiwiApi.types import Response


class SingletonABCMeta(abc.ABCMeta):
    """
    Abstract singleton metaclass, using for routers because in class methods
    it's not possible to get the router object,
    so we need singleton to get the same instances of routers

    """
    _instances: Dict[Any, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonABCMeta, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]


T = typing.TypeVar("T")


class BaseStorage(abc.ABC, typing.Generic[T]):
    """
    Абстрактный класс контроллера кэша

    """

    @abc.abstractmethod
    def clear(self, key: str, force: bool = False) -> Any:
        raise NotImplementedError

    def update_data(self, obj_to_cache: Any, key: Any) -> None:
        raise NotImplementedError

    def validate(self, kwargs: Dict[str, Any]) -> bool:
        """ Should validate some data from cache """


class AbstractRouter(metaclass=SingletonABCMeta):
    """Abstract class-router for building urls"""

    def __init__(self):
        self.config = self.setup_config()

    @abc.abstractmethod
    def setup_config(self) -> Any:
        raise NotImplementedError

    @staticmethod
    def _format_url_kwargs(url_: str, **kwargs: Any) -> Optional[str]:
        try:
            return url_.format(**kwargs)
        except KeyError:
            raise RuntimeError("Bad kwargs for url build")

    @abc.abstractmethod
    def build_url(self, api_method: str, **kwargs: Any) -> str:
        """Implementation of building url"""
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

    @abc.abstractmethod
    async def _make_request(
            self,
            url: str,
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
            ],
            get_bytes: bool,
            **kwargs) -> Response:
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

    @abc.abstractmethod
    async def close(self) -> None:  # pragma: no cover
        """
        Close client session
        """
        pass

    def raise_exception(
            self,
            status_code: str,
            json_info: Optional[Dict[str, Any]] = None,
            message: Optional[str] = None
    ) -> None:
        """Метод для обработки исключений и лучшего логирования"""

    async def __aenter__(self) -> AbstractParser:
        return self

    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_value: Optional[BaseException],
            traceback: Optional[TracebackType],
    ) -> None:
        await self.close()


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

    @abc.abstractmethod
    def _check_ip(self, ip_address: str) -> bool:
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
    async def post(self) -> Any:
        """
        Process POST request with basic IP validation.

        """
        self.validate_ip()

        update = await self.parse_update()

        self._hash_validator(update)

        await self.handler_manager.process_event(update)

    def _hash_validator(self, update) -> None:
        """ Validating by hash of update """

    @property
    def handler_manager(self) -> "Dispatcher":
        """ Return handler manager """
        return self.request.app.get(  # type: ignore
            self.app_key_handler_manager  # type: ignore
        )  # type: ignore
