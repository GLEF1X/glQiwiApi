from __future__ import annotations

import abc
from typing import Any, Generic, TypeVar, TYPE_CHECKING, Dict, Union

if TYPE_CHECKING:
    from glQiwiApi.qiwi.client import QiwiWrapper  # NOQA  # pragma: no cover
    from glQiwiApi.types.base import Base  # NOQA # pragma: no cover

T = TypeVar("T", bound=Union[Exception, "Base"])


class BaseHandlerMixin(Generic[T]):
    if TYPE_CHECKING:  # pragma: no cover
        event: T


class ClientMixin(Generic[T]):
    if TYPE_CHECKING:  # pragma: no cover
        event: T

    @property
    def client(self) -> "QiwiWrapper":
        return self.event.client

    @property
    def client_data(self) -> Dict[Any, Any]:
        return self.client.config_data


class Handler(abc.ABC, BaseHandlerMixin[T]):
    """Base class for all class-based handlers"""

    def __init__(self, event: T) -> None:
        self.event: T = event

    @abc.abstractmethod
    async def process_event(self) -> Any:  # pragma: no cover  # type: ignore
        raise NotImplementedError

    def __await__(self) -> Any:
        return self.process_event().__await__()
