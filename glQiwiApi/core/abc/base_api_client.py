from __future__ import annotations

import abc
import inspect
from copy import deepcopy
from types import TracebackType
from typing import TYPE_CHECKING as MYPY
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple, Type, TypeVar, Union

if MYPY:
    from glQiwiApi.core.request_service import RequestServiceProto  # pragma: no cover

T = TypeVar('T', bound='BaseAPIClient')

RequestServiceFactoryType = Callable[
    ..., Union[Awaitable['RequestServiceProto'], 'RequestServiceProto']
]

_C = TypeVar('_C', bound=Type['APIClientMeta'])


class APIClientMeta(abc.ABCMeta):
    """
    This metaclass fixes issue connected with poor release
    of glQiwiApi 2.0.5 that breaks all down. It's a complicated workaround of building of request service
    "on-flight" and allows users of API client to use custom factories of a request service.

    Due to limitations of aiohttp library that requires to create ClientSession only inside coroutine
    I have to write this metaclass to avoid additional viscous boilerplate code.
    """

    def __new__(
        mcs: Type[_C], name: str, bases: Tuple[Any, ...], attrs: Dict[str, Any], **kwargs: Any
    ) -> _C:
        for key, attribute in attrs.items():
            is_name_mangled = key.startswith('__')
            if is_name_mangled:
                continue

            if not inspect.iscoroutinefunction(attribute):
                continue

            if key in ('close', '_create_request_service', 'create_request_service'):
                continue

            def wrapper(m) -> Any:
                async def check_request_service_before_execute(self, *args: Any, **kw: Any) -> Any:
                    if self._request_service is None:
                        self._request_service = await self.create_request_service()

                    return await m(self, *args, **kw)

                return check_request_service_before_execute

            attrs[key] = wrapper(attrs[key])

        return super().__new__(mcs, name, bases, attrs, **kwargs)


class BaseAPIClient(metaclass=APIClientMeta):
    def __init__(
        self,
        request_service_factory: Optional[RequestServiceFactoryType] = None,
    ):
        self._request_service_factory = request_service_factory
        self._request_service: RequestServiceProto = None  # type: ignore

    async def __aenter__(self):  # type: ignore
        if self._request_service is None:
            self._request_service = await self.create_request_service()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def close(self) -> None:
        if self._request_service is None:
            return None

        await self._request_service.shutdown()

    async def create_request_service(self) -> RequestServiceProto:
        if self._request_service_factory is not None:
            if inspect.iscoroutinefunction(self._request_service_factory):
                return await self._request_service_factory(self)  # type: ignore
            return self._request_service_factory(self)  # type: ignore

        return await self._create_request_service()

    @abc.abstractmethod
    async def _create_request_service(self) -> RequestServiceProto:
        pass

    def __deepcopy__(self: T, memo: Dict[Any, Any]) -> T:
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            try:
                setattr(result, k, deepcopy(v, memo))
            except TypeError:
                pass
        return result
