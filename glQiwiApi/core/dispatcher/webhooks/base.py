from __future__ import annotations

import abc
from typing import Optional, Generic, TypeVar, TYPE_CHECKING, Tuple, cast, List, Any

from aiohttp import web

from glQiwiApi.core.dispatcher.dispatcher import Dispatcher

if TYPE_CHECKING:  # pragma: no cover
    from glQiwiApi.types.base import HashableBase  # pragma: no cover  # noqa

Event = TypeVar("Event", bound="HashableBase")


class UpdateHasAlreadyBeenProcessed(Exception):
    pass


class BaseWebHookView(web.View, Generic[Event]):
    """
    Base webhook view for processing events
    You can make own view and than use it in code,
    just inheriting this base class

    """

    app_key_check_ip: Optional[str] = None
    """app_key_check_ip stores key to a callable, which check ip"""

    app_key_dispatcher: Optional[str] = None
    """app_key_handler_dispatcher store Dispatcher instance to feed events to handlers"""

    _already_processed_object_hashes: List[int] = []

    @abc.abstractmethod
    async def parse_update(self) -> Event:
        raise NotImplementedError

    def check_ip(self) -> Tuple[Optional[str], bool]:
        """
        Check client IP. Accept requests only from telegram servers.

        :return:
        """
        if self.app_key_check_ip is None:
            raise RuntimeError(
                "There is no check_ip function to validate ip."
                " Please, override `app_key_check_ip` attribute"
            )

        check_ip_function = self.request.app.get(self.app_key_check_ip, False)

        # For reverse proxy (nginx)
        forwarded_for = self.request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for, check_ip_function(forwarded_for)

        # For default method
        peer_name = self.request.transport.get_extra_info("peername")  # type: ignore
        if peer_name is not None:
            host, _ = peer_name
            return cast(Optional[str], host), check_ip_function(host)

        # Not allowed and can't get client IP
        return None, False

    def validate_ip(self) -> None:
        """
        Check ip if that is needed. Raise web.HTTPUnauthorized for not allowed hosts.
        """
        if self.request.app.get(self.app_key_check_ip, False):  # type: ignore
            ip_address, accept = self.check_ip()
            if not accept:
                self.dispatcher.logger.warning(
                    f"Blocking request from an unauthorized IP: {ip_address}"
                )
                raise web.HTTPUnauthorized()
        return None  # hint for mypy

    async def process_event(self, event: Event) -> None:
        await self.dispatcher.process_event(event)

    async def post(self) -> web.Response:
        """
        Process POST request with basic IP validation.

        """
        self.validate_ip()
        event = await self.parse_update()

        try:
            self.avoid_multiply_events_collision(event)
        except UpdateHasAlreadyBeenProcessed:
            return self.ok_response()

        self._validate_event_signature(event)
        await self.process_event(event)
        return self.ok_response()

    async def get(self):
        self.validate_ip()
        return web.Response(text="")

    @abc.abstractmethod
    def ok_response(self) -> web.Response:
        ...

    @abc.abstractmethod
    def _validate_event_signature(self, update: Event) -> None:
        raise NotImplementedError

    @property
    def dispatcher(self) -> Dispatcher:
        if self.app_key_dispatcher is None:
            raise RuntimeError(
                "There is no check_ip function to validate ip."
                " Please, override `app_key_dispatcher` attribute"
            )
        return self.request.app[self.app_key_dispatcher]

    def avoid_multiply_events_collision(self, event: Event) -> Any:
        """
        QIWI API can send the same update twice or more, so we need to avoid this problem anyway.
        Also, you can override it with redis usage or more advanced hashing.
        """
        event_hash = hash(event)
        if any(
            event_hash == processed_hash
            for processed_hash in self._already_processed_object_hashes
        ):
            raise UpdateHasAlreadyBeenProcessed()

        self._already_processed_object_hashes.append(event_hash)
