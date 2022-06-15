import abc
import logging
from typing import TYPE_CHECKING as MYPY
from typing import Any, Generic, Type, TypeVar

from aiohttp import web
from aiohttp.web_request import Request

from glQiwiApi.core.event_fetching.dispatcher import BaseDispatcher
from glQiwiApi.core.event_fetching.webhooks.dto.errors import WebhookAPIError
from glQiwiApi.core.event_fetching.webhooks.services.collision_detector import (
    AbstractCollisionDetector,
    UnexpectedCollision,
)
from glQiwiApi.utils.compat import json

if MYPY:
    from glQiwiApi.types.base import HashableBase  # noqa

Event = TypeVar('Event', bound='HashableBase')

logger = logging.getLogger('glQiwiApi.webhooks.base')


class BaseWebhookView(web.View, Generic[Event]):
    """
    Generic webhook view for processing events
    You can make your own view and than use it in code, just inheriting this base class

    """

    def __init__(
        self,
        request: Request,
        dispatcher: BaseDispatcher,
        collision_detector: AbstractCollisionDetector[Any],
        event_cls: Type[Event],
        encryption_key: str,
    ) -> None:
        super().__init__(request)
        self._dispatcher = dispatcher
        self._collision_detector = collision_detector
        self._event_cls = event_cls
        self._encryption_key = encryption_key

    @abc.abstractmethod
    async def ok_response(self) -> web.Response:
        pass

    async def get(self) -> web.Response:
        return web.Response(text='')

    async def post(self) -> web.Response:
        event = await self._parse_raw_request()

        try:
            self._collision_detector.remember_processed_object(event)
        except UnexpectedCollision:
            logger.debug('Detect collision on event %s', event)
            return await self.ok_response()

        self._validate_event_signature(event)
        await self.process_event(event)
        return await self.ok_response()

    async def _parse_raw_request(self) -> Event:
        """Parse raw update and return pydantic model"""
        try:
            data = await self.request.json(loads=json.loads)
            if isinstance(data, str):
                return self._event_cls.parse_raw(data)
            elif isinstance(data, dict):  # pragma: no cover
                return self._event_cls.parse_obj(data)
            else:
                raise ValueError()
        except ValueError:
            raise web.HTTPBadRequest(
                text=WebhookAPIError(status='Validation error').json(),
                content_type='application/json',
            )

    @abc.abstractmethod
    def _validate_event_signature(self, update: Event) -> None:
        raise NotImplementedError

    async def process_event(self, event: Event) -> None:
        await self._dispatcher.process_event(event)
