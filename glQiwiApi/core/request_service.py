from typing import Dict, Optional, Any, Union, cast

import aiohttp
from aiohttp import ClientTimeout, ServerDisconnectedError, \
    ClientProxyConnectionError, ClientConnectionError
from aiohttp.typedefs import LooseCookies

from glQiwiApi.core.abstracts import AbstractRouter
from glQiwiApi.core.constants import DEFAULT_CACHE_TIME
from glQiwiApi.core.session.pool import AbstractSessionPool, AiohttpSessionPool
from glQiwiApi.core.storage import InMemoryCacheStorage, APIResponsesCacheInvalidationStrategy, \
    CachedAPIRequest, Payload
from glQiwiApi.utils.exceptions import APIError
from glQiwiApi.utils.payload import make_payload, check_result


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
            messages: Optional[Dict[int, str]] = None,
            cache_time: Union[float, int] = DEFAULT_CACHE_TIME,
            session_pool: Optional[AbstractSessionPool[Any]] = None,
    ) -> None:
        self._base_headers = {
            "User-Agent": "glQiwiApi/stable",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        self.messages = messages or EmptyMessages()
        self._timeout = ClientTimeout(
            total=5, connect=None, sock_connect=5, sock_read=None
        )
        if session_pool is None:
            session_pool = AiohttpSessionPool()
        self._cache = InMemoryCacheStorage(
            invalidate_strategy=APIResponsesCacheInvalidationStrategy(cache_time=cache_time)
        )
        self._session_pool: AbstractSessionPool[Any] = session_pool

    def reset_cache(self) -> None:
        self._cache.clear()

    async def warmup_session_pool(self) -> None:
        await self._session_pool.get()

    async def send_request(
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
        return await self.make_request(
            url,
            http_method,
            set_timeout=set_timeout,
            headers=headers,
            json=json,
            data=data,
            params=params,
            cookies=cookies,
        )

    async def make_request(
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
        request_args = {
            k: v for k, v in locals().items() if not isinstance(v, type(self))
        }
        if await self._cache_has_similar_cached_response(**request_args):
            return (await self._cache.retrieve(url)).response  # type: ignore
        async with self._session_pool.acquire() as session:
            try:
                resp = await session.request(
                    method=method,
                    url=url,
                    data=data,
                    headers=headers,
                    json=json if isinstance(json, dict) else None,
                    cookies=cookies,
                    params=params,
                    **kwargs,
                )
                response = check_result(
                    self.messages,
                    resp.status,
                    resp.request_info,
                    await resp.text(),
                )
            except (
                    ClientProxyConnectionError,
                    ServerDisconnectedError,
                    ClientConnectionError,
            ):
                raise self.make_exception(status_code=500)
            else:
                self._cache_result(response, **request_args)
                return response

    async def _cache_has_similar_cached_response(self, **request_args: Any) -> bool:
        return await self._cache.contains_similar(Payload(**request_args))

    def _cache_result(self, response: Any, method: str, **kwargs: Any) -> None:
        self._cache.update(
            **{
                kwargs["url"]: CachedAPIRequest(
                    payload=Payload(**kwargs),
                    response=response,
                    method=method
                )
            }
        )

    def make_exception(
            self,
            status_code: int,
            traceback_info: Optional[
                Union[aiohttp.RequestInfo, Dict[Any, Any], str, bytes]
            ] = None,
            message: Optional[str] = None,
    ) -> APIError:
        """Raise :class:`APIError` exception with pretty explanation"""
        from glQiwiApi import __version__

        if not isinstance(message, str) and isinstance(self.messages, dict):
            message = self.messages.get(status_code, "Unknown")
        return APIError(
            message,
            status_code,
            additional_info=f"{__version__} version api",
            traceback_info=traceback_info,
        )

    @classmethod
    def filter_dict(cls, dictionary: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Pop NoneType values and convert everything to str, designed?for=params

        :param dictionary: source dict
        :return: filtered dict
        """
        return {k: str(v) for k, v in dictionary.items() if v is not None}

    async def text_content(
            self,
            url: str,
            method: str,
            set_timeout: bool = True,
            cookies: Optional[LooseCookies] = None,
            json: Optional[Any] = None,
            data: Optional[Any] = None,
            headers: Optional[Any] = None,
            params: Optional[Any] = None,
            encoding: Optional[str] = None,
    ) -> str:
        prepared_payload = make_payload(**locals())
        async with self._session_pool.acquire() as session:
            resp = await session.request(
                method=method,
                url=url,
                **prepared_payload
            )
        return cast(str, resp)

    async def retrieve_bytes(self, url: str, method: str, **kwargs: Any) -> bytes:
        async with self._session_pool.acquire() as session:
            resp = await session.request(method, url, **kwargs)
        return cast(bytes, await resp.read())
