import logging
from typing import Any, Dict, Optional, TypeVar, cast

from aiohttp.typedefs import LooseCookies

from glQiwiApi.core.abc.api_method import APIMethod
from glQiwiApi.core.cache.cached_types import CachedAPIRequest, Payload
from glQiwiApi.core.cache.storage import CacheStorage
from glQiwiApi.core.session.holder import AbstractSessionHolder, AiohttpSessionHolder, HTTPResponse
from glQiwiApi.utils.compat import Protocol
from glQiwiApi.utils.payload import make_payload

logger = logging.getLogger("glQiwiApi.RequestService")

T = TypeVar("T")


class RequestServiceProto(Protocol):
    async def execute_api_method(self, method: APIMethod[T], **url_kw: Any) -> T:
        ...

    async def get_json_content(
        self,
        url: str,
        method: str,
        cookies: Optional[LooseCookies] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Any] = None,
        params: Optional[Any] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        ...

    async def send_request(
        self,
        url: str,
        method: str,
        cookies: Optional[LooseCookies] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Any] = None,
        params: Optional[Any] = None,
        **kwargs: Any,
    ) -> HTTPResponse:
        ...

    async def warmup(self) -> Any:
        ...

    async def shutdown(self) -> None:
        ...


class RequestService:
    def __init__(
        self,
        session_holder: Optional[AbstractSessionHolder[Any]] = None,
        base_headers: Optional[Dict[str, Any]] = None,
        **session_holder_kw: Any,
    ) -> None:
        if session_holder is None:
            session_holder = AiohttpSessionHolder(headers=base_headers)
        self._session_holder = session_holder

        self._session_holder.update_session_kwargs(**session_holder_kw)

    async def execute_api_method(self, method: APIMethod[T], **url_kw: Any) -> T:
        request = method.build_request(**url_kw)
        raw_http_response = await self.send_request(
            request.endpoint,
            request.http_method,
            params=request.params,
            data=request.data,
            headers=request.headers,
            json=request.json_payload,
        )
        return method.parse_http_response(raw_http_response)

    async def get_json_content(
        self,
        url: str,
        method: str,
        cookies: Optional[LooseCookies] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Any] = None,
        params: Optional[Any] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        prepared_payload = make_payload(**locals(), exclude=("kwargs",))
        response = await self.send_request(**prepared_payload)
        return response.json()

    async def warmup(self) -> Any:
        return await self._session_holder.get_session()

    async def shutdown(self) -> None:
        await self._session_holder.close()

    async def send_request(
        self,
        url: str,
        method: str,
        cookies: Optional[LooseCookies] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Any] = None,
        params: Optional[Any] = None,
        **kwargs: Any,
    ) -> HTTPResponse:
        session = await self._session_holder.get_session()
        return await self._session_holder.convert_third_party_lib_response_to_http_response(
            await session.request(
                method=method,
                url=url,
                data=data,
                headers=headers,
                json=json,
                cookies=cookies,
                params=params,
                **kwargs,
            )
        )


class RequestServiceCacheDecorator(RequestServiceProto):
    def __init__(
        self,
        request_service: RequestServiceProto,
        cache_storage: CacheStorage,
    ) -> None:
        self._cache = cache_storage
        self._request_service = request_service

    async def execute_api_method(self, method: APIMethod[T], **url_kw: Any) -> T:
        return await self._request_service.execute_api_method(method, **url_kw)

    async def get_json_content(
        self,
        url: str,
        method: str,
        cookies: Optional[LooseCookies] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Any] = None,
        params: Optional[Any] = None,
        **kwargs: Any,
    ) -> Dict[Any, Any]:
        request_args = make_payload(**locals())

        if await self._cache.contains_similar(Payload(**request_args)):
            return cast(Dict[Any, Any], (await self._cache.retrieve(url)).response)

        response = await self._request_service.get_json_content(**request_args)
        await self._cache_response(response, **request_args)
        return response

    async def send_request(
        self,
        url: str,
        method: str,
        cookies: Optional[LooseCookies] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Any] = None,
        params: Optional[Any] = None,
        **kwargs: Any,
    ) -> HTTPResponse:
        return await self._request_service.send_request(
            url, method, cookies, json, data, headers, params, **kwargs
        )

    async def warmup(self) -> Any:
        return await self._request_service.shutdown()

    async def shutdown(self) -> None:
        await self._request_service.shutdown()

    async def _cache_response(self, response: Any, method: str, **kwargs: Any) -> None:
        await self._cache.update(
            **{
                kwargs["endpoint"]: CachedAPIRequest(
                    payload=Payload(**kwargs), response=response, method=method
                )
            }
        )
