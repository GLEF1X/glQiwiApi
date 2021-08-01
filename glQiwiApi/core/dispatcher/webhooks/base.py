from __future__ import annotations

import abc
from typing import Optional, Union, Tuple, Generic, TypeVar, TYPE_CHECKING

from aiohttp import web

from glQiwiApi.core.dispatcher.dispatcher import Dispatcher

if TYPE_CHECKING:  # pragma: no cover
    from glQiwiApi.types.base import Base  # pragma: no cover  # noqa

T = TypeVar("T", bound="Base")


class BaseWebHookView(web.View, Generic[T]):
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

    @abc.abstractmethod
    async def parse_update(self) -> T:
        """parse_update method that deals with marshaling json"""
        raise NotImplementedError

    def validate_ip(self) -> None:
        """validating request ip address"""
        if self.request.app.get(self.app_key_check_ip):  # type: ignore
            ip_addr_data = self.check_ip()
            if not ip_addr_data[1]:
                raise web.HTTPUnauthorized()
        return None

    def check_ip(self) -> Union[Tuple[str, bool], Tuple[None, bool]]:
        """checking ip, using headers or peer_name"""
        forwarded_for = self.request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for, self._check_ip(forwarded_for)
        peer_name = self.request.transport.get_extra_info("peername")  # type: ignore

        if peer_name is not None:
            host, _ = peer_name
            return host, self._check_ip(host)

        return None, False

    async def post(self) -> web.Response:
        """
        Process POST request with basic IP validation.

        """
        self.validate_ip()
        update = await self.parse_update()
        self._hash_validator(update)
        await self.handler_manager.feed_event(update)
        return web.Response(text="ok")

    def _hash_validator(self, update: T) -> None:
        """Validating by hash of update"""

    @property
    def handler_manager(self) -> Dispatcher:
        return self.request.app[self.app_key_handler_manager]  # type: ignore
