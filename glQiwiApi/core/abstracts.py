from __future__ import annotations

import abc
import typing
from types import TracebackType
from typing import Optional, Dict, Any, Type

from aiohttp import RequestInfo
from aiohttp.typedefs import LooseCookies


class SingletonABCMeta(abc.ABCMeta):
    """
    Abstract singleton metaclass, using for routers because in class methods
    it's not possible to get the router object,
    so we need singleton to get the same instances of routers

    """

    _instances: Dict[Any, Any] = {}

    def __call__(cls, *args, **kwargs):  # type: ignore
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonABCMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class BaseStorage(abc.ABC):
    @abc.abstractmethod
    def clear(self, key: typing.Optional[str] = None, *, force: bool = False) -> Any:
        raise NotImplementedError

    def update_data(self, obj_to_cache: Any, key: Any) -> None:
        raise NotImplementedError

    def validate(self, **kwargs: Any) -> bool:
        """Should validate some data from cache"""


class AbstractRouter(metaclass=SingletonABCMeta):
    """Abstract class-router for building urls"""

    def __init__(self) -> None:
        self.config = self.setup_config()
        self.routes = self.setup_routes()

    @abc.abstractmethod
    def setup_config(self) -> Any:
        raise NotImplementedError

    @abc.abstractmethod
    def setup_routes(self) -> Any:
        raise NotImplementedError

    @staticmethod
    def _format_url_kwargs(url_: str, **kwargs: Any) -> str:
        try:
            return url_.format(**kwargs)
        except KeyError:
            raise TypeError("Bad kwargs for url assembly")

    @abc.abstractmethod
    def build_url(self, api_method: str, **kwargs: Any) -> str:
        """Implementation of building url"""
        raise NotImplementedError


class AbstractParser(abc.ABC):
    """Abstract class of parser for send request to different API's"""

    @abc.abstractmethod
    async def make_request(
        self,
        url: str,
        method: str,
        set_timeout: bool = True,
        cookies: Optional[LooseCookies] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Any] = None,
        params: Optional[Any] = None,
        **kwargs: Any
    ) -> Dict[Any, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    async def close(self) -> None:  # pragma: no cover
        """
        Close client session
        """
        pass

    @abc.abstractmethod
    def make_exception(
        self,
        status_code: int,
        traceback_info: Optional[RequestInfo] = None,
        message: Optional[str] = None,
    ) -> Exception:
        raise NotImplementedError

    async def __aenter__(self) -> AbstractParser:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()
