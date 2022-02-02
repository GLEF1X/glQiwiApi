import logging
from typing import Any, Dict, Optional, TypeVar, Protocol

from aiohttp.typedefs import LooseCookies
from pydantic import BaseModel

from glQiwiApi.base.api_method import APIMethod
from glQiwiApi.core.cache.cached_types import CachedAPIRequest, Payload
from glQiwiApi.core.cache.storage import CacheStorage
from glQiwiApi.core.session.holder import AbstractSessionHolder, AiohttpSessionHolder, Response
from glQiwiApi.utils.payload import make_payload, decode_response_as_json

logger = logging.getLogger("glQiwiApi.RequestService")


T = TypeVar("T")


class RequestServiceProto(Protocol):
    async def emit_request_to_api(self, method: APIMethod[T], **url_kw: Any) -> T: ...

    async def get_text_content(
            self,
            url: str,
            method: str,
            cookies: Optional[LooseCookies] = None,
            json: Optional[Any] = None,
            data: Optional[Any] = None,
            headers: Optional[Any] = None,
            params: Optional[Any] = None,
    ) -> str: ...

    async def get_binary_content(self, url: str, method: str, **kwargs: Any) -> bytes: ...

    async def get_json_content(self, url: str,
                               method: str,
                               cookies: Optional[LooseCookies] = None,
                               json: Optional[Any] = None,
                               data: Optional[Any] = None,
                               headers: Optional[Any] = None,
                               params: Optional[Any] = None,
                               **kwargs: Any) -> Dict[Any, Any]: ...

    async def warmup(self) -> Any: ...

    async def shutdown(self) -> None: ...


class RequestService:

    def __init__(
            self,
            session_holder: Optional[AbstractSessionHolder[Any]] = None,
            base_headers: Optional[Dict[str, Any]] = None,
            **session_holder_kw: Any
    ) -> None:
        if session_holder is None:
            session_holder = AiohttpSessionHolder(headers=base_headers)
        self._session_holder = session_holder

        self._session_holder.update_session_kwargs(**session_holder_kw)

    async def emit_request_to_api(self, method: APIMethod[R], **url_kw: Any) -> R:
        request = method.build_request(**url_kw)
        return method.parse_response(
            await self.get_json_content(
                request.endpoint,
                request.http_method,
                params=request.params,
                data=request.data,
                headers=request.headers
            )
        )

    async def get_text_content(
            self,
            url: str,
            method: str,
            cookies: Optional[LooseCookies] = None,
            json: Optional[Any] = None,
            data: Optional[Any] = None,
            headers: Optional[Any] = None,
            params: Optional[Any] = None,
    ) -> str:
        prepared_payload = make_payload(**locals())
        response = await self._send_request(**prepared_payload)
        return response.body.decode(encoding="utf-8")

    async def get_binary_content(self, url: str, method: str, **kwargs: Any) -> bytes:
        return (await self._send_request(url, method, **kwargs)).body

    async def get_json_content(self, url: str,
                               method: str,
                               cookies: Optional[LooseCookies] = None,
                               json: Optional[Any] = None,
                               data: Optional[Any] = None,
                               headers: Optional[Any] = None,
                               params: Optional[Any] = None,
                               **kwargs: Any) -> Dict[Any, Any]:
        prepared_payload = make_payload(**locals(), exclude=("kwargs", ))
        response = await self._send_request(**prepared_payload)
        return decode_response_as_json(response)

    async def warmup(self) -> Any:
        return await self._session_holder.get_session()

    async def shutdown(self) -> None:
        await self._session_holder.close()

    async def _send_request(
            self,
            url: str,
            method: str,
            cookies: Optional[LooseCookies] = None,
            json: Optional[Any] = None,
            data: Optional[Any] = None,
            headers: Optional[Any] = None,
            params: Optional[Any] = None,
            **kwargs: Any,
    ) -> Response:
        session = await self._session_holder.get_session()
        return await self._session_holder.parse_response(await session.request(
            method=method,
            url=url,
            data=data,
            headers=headers,
            json=json,
            cookies=cookies,
            params=params,
            **kwargs,
        ))


class RequestServiceCacheDecorator(RequestServiceProto):

    def __init__(
            self,
            request_service: RequestServiceProto,
            cache_storage: CacheStorage,
    ) -> None:
        self._cache = cache_storage
        self._request_service = request_service

    async def emit_request_to_api(self, method: APIMethod[T], **url_kw: Any) -> T:
        return await self._request_service.emit_request_to_api(method, **url_kw)

    async def get_text_content(self, url: str, method: str, cookies: Optional[LooseCookies] = None,
                               json: Optional[Any] = None, data: Optional[Any] = None,
                               headers: Optional[Any] = None, params: Optional[Any] = None) -> str:
        request_args = make_payload(**locals())
        response = await self._request_service.get_text_content(**request_args)
        await self._cache_response(response, method, **request_args)
        return response

    async def get_json_content(self, url: str,
                               method: str,
                               cookies: Optional[LooseCookies] = None,
                               json: Optional[Any] = None,
                               data: Optional[Any] = None,
                               headers: Optional[Any] = None,
                               params: Optional[Any] = None,
                               **kwargs: Any) -> Dict[Any, Any]:
        request_args = make_payload(**locals())

        if await self._cache.contains_similar(Payload(**request_args)):
            return (await self._cache.retrieve(url)).response

        response = await self._request_service.get_json_content(**request_args)
        await self._cache_response(response, **request_args)
        return response

    async def get_binary_content(self, url: str, method: str, **kwargs: Any) -> bytes:
        return await self._request_service.get_binary_content(url, method, **kwargs)

    async def warmup(self) -> Any:
        return await self._request_service.shutdown()

    async def shutdown(self) -> None:
        await self._request_service.shutdown()

    async def _cache_response(self, response: Any, method: str, **kwargs: Any) -> None:
        await self._cache.update(
            **{
                kwargs["url"]: CachedAPIRequest(
                    payload=Payload(**kwargs), response=response, method=method
                )
            }
        )
