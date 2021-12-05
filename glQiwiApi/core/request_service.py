from __future__ import annotations

import logging
import uuid
from typing import Dict, Optional, Any, Union, cast

from aiohttp import ClientTimeout, ServerDisconnectedError, \
    ClientProxyConnectionError, ClientConnectionError, RequestInfo, ClientSession
from aiohttp.typedefs import LooseCookies

from glQiwiApi.core.abc.router import AbstractRouter
from glQiwiApi.core.constants import NO_CACHING
from glQiwiApi.core.session.holder import AbstractSessionHolder, AiohttpSessionHolder
from glQiwiApi.core.storage import InMemoryCacheStorage, APIResponsesCacheInvalidationStrategy, \
    CachedAPIRequest, Payload
from glQiwiApi.utils.exceptions import APIError
from glQiwiApi.utils.payload import make_payload, get_decoded_result

logger = logging.getLogger("glQiwiApi.RequestService")


class EmptyMessages(Dict[Any, Any]):
    EMPTY_STRING = ""

    def __init__(self) -> None:
        super().__init__({})

    def __getattr__(self, item: Any) -> Any:
        return self.EMPTY_STRING


class RequestService:
    """
    Deal with :class:`Storage`,
    caching queries and managing stable work of sending requests

    """

    def __init__(
            self,
            error_messages: Optional[Dict[int, str]] = None,
            cache_time: Union[float, int] = NO_CACHING,
            session_holder: Optional[AbstractSessionHolder[Any]] = None,
    ) -> None:
        if session_holder is None:
            session_holder = AiohttpSessionHolder(
                timeout=ClientTimeout(total=5, connect=None, sock_connect=5, sock_read=None)
            )
        self.error_messages = error_messages or EmptyMessages()
        self._cache = InMemoryCacheStorage(
            invalidate_strategy=APIResponsesCacheInvalidationStrategy(cache_time=cache_time),
        )
        self._session_holder: AbstractSessionHolder[Any] = session_holder

    async def api_request(
            self,
            http_method: str,
            api_method: str,
            router: AbstractRouter,
            set_timeout: bool = True,
            cookies: Optional[LooseCookies] = None,
            json: Optional[Any] = None,
            data: Optional[Dict[Any, Any]] = None,
            headers: Optional[Dict[Any, Any]] = None,
            params: Optional[Dict[Any, Any]] = None,
            **kwargs: Any
    ) -> Dict[Any, Any]:
        url = router.build_url(api_method, **kwargs)
        return await self.raw_request(
            url,
            http_method,
            set_timeout=set_timeout,
            headers=headers,
            json=json,
            data=data,
            params=params,
            cookies=cookies,
        )

    async def raw_request(
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
        request_args = {k: v for k, v in locals().items() if not isinstance(v, type(self))}
        if await self._storage_has_similar_cached_response(**request_args):
            return (await self._cache.retrieve(url)).response  # type: ignore
        session = await self._session_holder.get_session()
        _request_id = uuid.uuid4().hex
        try:
            logger.debug(
                "Send request %s to %s body = %s params = %s headers = %s json = %s",
                _request_id, url, data, params, headers, json
            )
            http_response = await session.request(
                method=method,
                url=url,
                data=data,
                headers=headers,
                json=json if isinstance(json, dict) else None,
                cookies=cookies,
                params=params,
                **kwargs,
            )
            decoded_response = get_decoded_result(
                self.error_messages,
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
                decoded_response
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
        logger.debug("Get text content from %s method = %s json = %s body = %d headers = %s params = %s ",
                     url, method, json, data, headers, params)
        prepared_payload = make_payload(**locals())
        session: ClientSession = await self._session_holder.get_session()
        resp = await session.request(**prepared_payload)
        return cast(str, resp)

    async def retrieve_bytes(self, url: str, method: str, **kwargs: Any) -> bytes:
        session = await self._session_holder.get_session()
        resp = await session.request(method, url, **kwargs)
        return cast(bytes, await resp.read())

    async def _storage_has_similar_cached_response(self, **request_args: Any) -> bool:
        return await self._cache.contains_similar(Payload(**request_args))

    def _cache_result(self, response: Any, method: str, **kwargs: Any) -> None:
        logger.debug("Cache response %s kwargs = %s", response, kwargs)
        self._cache.update(
            **{
                kwargs["url"]: CachedAPIRequest(
                    payload=Payload(**kwargs),
                    response=response,
                    method=method
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

        if not isinstance(message, str) and isinstance(self.error_messages, dict):
            message = self.error_messages.get(status_code, "Unknown")
        return APIError(
            message,
            status_code,
            additional_info=f"{__version__} API version",
            traceback_info=traceback_info,
        )

    def reset_cache(self) -> None:
        self._cache.clear()

    async def warmup(self) -> Any:
        return await self._session_holder.get_session()

    async def shutdown(self) -> None:
        await self._session_holder.close()
