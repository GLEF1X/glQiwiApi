from __future__ import annotations

import abc
from typing import Optional, Generic, TypeVar, TYPE_CHECKING, Tuple, cast, Any, Type

from aiohttp import web
from pydantic import ValidationError

from glQiwiApi.core.dispatcher.implementation import Dispatcher
from glQiwiApi.core.dispatcher.webhooks.collision_detectors import HashBasedCollisionDetector, \
    UnexpectedCollision

if TYPE_CHECKING:  # pragma: no cover
    from glQiwiApi.types.base import HashableBase  # pragma: no cover  # noqa

Event = TypeVar("Event", bound="HashableBase")


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

    collision_detector: HashBasedCollisionDetector[Event] = HashBasedCollisionDetector()
    """
    QIWI API can send the same update twice or more, so we need to avoid this problem anyway.
    Also, you can override it with redis usage or more advanced hashing.
    """

    _event_type: Type[Event]
    """Need to be overriden"""

    async def parse_update(self) -> Event:
        """Parse raw update and return pydantic model"""
        data = await self._json_body()
        try:
            if isinstance(data, str):
                return self._event_type.parse_raw(data)
            elif isinstance(data, dict):
                return self._event_type.parse_obj(data)
            else:
                raise ValidationError
        except ValidationError:
            raise web.HTTPBadRequest()

    async def _json_body(self) -> Any:
        try:
            import orjson as json
        except ImportError:
            import json  # type: ignore

        text = await self.request.text()
        return json.loads(text)

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
            self.collision_detector.remember_processed_object(event)
        except UnexpectedCollision:
            self.dispatcher.logger.debug("Detect collision on event")
            return self.ok_response()

        self._validate_event_signature(event)
        await self.process_event(event)
        return self.ok_response()

    async def get(self) -> web.Response:
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
        return cast(Dispatcher, self.request.app[self.app_key_dispatcher])
