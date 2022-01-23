from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional, Union, cast, TypeVar

from aiohttp import (
    ClientConnectionError,
    ClientProxyConnectionError,
    ClientSession,
    ClientTimeout,
    RequestInfo,
    ServerDisconnectedError,
)
from aiohttp.typedefs import LooseCookies
from pydantic import BaseModel

from glQiwiApi.base.api_method import APIMethod
from glQiwiApi.core.cache import APIResponsesCacheInvalidationStrategy, InMemoryCacheStorage
from glQiwiApi.core.cache.cached_types import CachedAPIRequest, Payload
from glQiwiApi.core.session.holder import AbstractSessionHolder, AiohttpSessionHolder
from glQiwiApi.qiwi.exceptions import APIError
from glQiwiApi.utils.payload import get_decoded_result, make_payload

logger = logging.getLogger("glQiwiApi.RequestService")


class EmptyMessages(Dict[Any, Any]):
    def __init__(self) -> None:
        super().__init__({})

    def __getattr__(self, item: Any) -> Any:
        return ""  # pragma: no cover


R = TypeVar("R")


class RequestService:
    """
    Deal with :class:`Storage`,
    caching queries and managing stable work of sending requests

    """

    def __init__(
            self,
            error_messages: Optional[Dict[int, str]] = None,
            cache_time: Union[float, int] = 0,
            session_holder: Optional[AbstractSessionHolder[Any]] = None,
            base_headers: Optional[Dict[str, Any]] = None,
            **session_holder_kw: Any
    ) -> None:
        if session_holder is None:
            session_holder = AiohttpSessionHolder(headers=base_headers)
        self._error_messages = error_messages or EmptyMessages()
        self._cache = InMemoryCacheStorage(
            invalidate_strategy=APIResponsesCacheInvalidationStrategy(
                cache_time_in_seconds=cache_time
            ),
        )
        self._session_holder: AbstractSessionHolder[Any] = session_holder

        self._session_holder.update_session_kwargs(**session_holder_kw)

    async def emit_request_to_api(self, method: APIMethod[R], **url_kw: Any) -> R:
        request = method.build_request(**url_kw)
        return method.parse_response(
            await self.emit_request(
                request.endpoint,
                request.http_method,
                params=request.params,
                data=request.data,
                headers=request.headers
            )
        )

    async def emit_request(
            self,
            url: str,
            method: str,
            set_timeout: bool = True,
            cookies: Optional[LooseCookies] = None,
            json: Optional[Any] = None,
            data: Optional[Any] = None,
            headers: Optional[Any] = None,
            params: Optional[Any] = None,
            **kwargs: Any,
    ) -> Dict[Any, Any]:
        request_args = {k: v for k, v in locals().items() if not isinstance(v, type(self))}
        if self._storage_has_similar_cached_response(**request_args):
            return self._cache.retrieve(url).response  # type: ignore
        session = await self._session_holder.get_session()
        _request_id = uuid.uuid4().hex
        try:
            logger.debug(
                "Send request %s to %s body = %s params = %s headers = %s json = %s",
                _request_id,
                url,
                data,
                params,
                headers,
                json,
            )
            http_response = await session.request(
                method=method,
                url=url,
                data=data,
                headers=headers,
                json=json,
                cookies=cookies,
                params=params,
                **kwargs,
            )
            decoded_response = get_decoded_result(
                self._error_messages,
                http_response.status,
                http_response.request_info,
                await http_response.text(),
            )
        except (
                ClientProxyConnectionError,
                ServerDisconnectedError,
                ClientConnectionError,
        ):
            raise self.api_exception(status_code=500)
        else:
            logger.debug(
                "Request %s is successful status = %d decoded response = %s",
                _request_id,
                http_response.status,
                decoded_response,
            )
            self._cache_result(decoded_response, **request_args)
            return decoded_response

    async def text_content(
            self,
            url: str,
            method: str,
            cookies: Optional[LooseCookies] = None,
            json: Optional[Any] = None,
            data: Optional[Any] = None,
            headers: Optional[Any] = None,
            params: Optional[Any] = None,
    ) -> str:
        logger.debug(
            "Get text content from %s method = %s json = %s body = %d headers = %s params = %s ",
            url,
            method,
            json,
            data,
            headers,
            params,
        )
        prepared_payload = make_payload(**locals())
        session: ClientSession = await self._session_holder.get_session()
        resp = await session.request(**prepared_payload)
        return cast(str, resp)

    async def retrieve_bytes(self, url: str, method: str, **kwargs: Any) -> bytes:
        session = await self._session_holder.get_session()
        resp = await session.request(method, url, **kwargs)
        return cast(bytes, await resp.read())

    def _storage_has_similar_cached_response(self, **request_args: Any) -> bool:
        return self._cache.contains_similar(Payload(**request_args))

    def _cache_result(self, response: Any, method: str, **kwargs: Any) -> None:
        logger.debug("Put response in cache %s kwargs = %s", response, kwargs)
        self._cache.update(
            **{
                kwargs["url"]: CachedAPIRequest(
                    payload=Payload(**kwargs), response=response, method=method
                )
            }
        )

    def api_exception(
            self,
            status_code: int,
            traceback_info: Optional[Union[RequestInfo, Dict[Any, Any], str, bytes]] = None,
            message: Optional[str] = None,
    ) -> APIError:
        """Raise :class:`APIError` exception with pretty explanation"""
        from glQiwiApi import __version__

        if not isinstance(message, str) and isinstance(self._error_messages, dict):
            message = self._error_messages.get(status_code, "Unknown")
        return APIError(
            message,
            status_code,
            additional_info=f"{__version__} API version",
            request_data=traceback_info,
        )

    def reset_cache(self) -> None:
        self._cache.clear()

    async def warmup(self) -> Any:
        return await self._session_holder.get_session()

    async def shutdown(self) -> None:
        await self._session_holder.close()
