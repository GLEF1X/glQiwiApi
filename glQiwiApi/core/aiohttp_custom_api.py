from typing import Dict, Optional, Any, Union

import aiohttp
from aiohttp.typedefs import LooseCookies

from glQiwiApi.core.abstracts import AbstractRouter
from glQiwiApi.core.basic_requests_api import HttpXParser, _ProxyType
from glQiwiApi.core.constants import DEFAULT_CACHE_TIME
from glQiwiApi.core.storage import Storage
from glQiwiApi.utils import exceptions
from glQiwiApi.utils.payload import make_payload


class RequestManager(HttpXParser):
    """
    Deal with :class:`Storage`,
    caching queries and managing stable work of sending requests

    """

    __slots__ = (
        "without_context",
        "messages",
        "_cache",
        "_should_reset_connector",
        "_connector_type",
        "_connector_init",
        "_proxy",
    )

    def __init__(
        self,
        without_context: bool = False,
        messages: Optional[Dict[int, str]] = None,
        cache_time: Union[float, int] = DEFAULT_CACHE_TIME,
        proxy: Optional[_ProxyType] = None,
    ) -> None:
        super(RequestManager, self).__init__(proxy=proxy, messages=messages)

        self.without_context: bool = without_context
        self._cache = Storage(cache_time=cache_time)

    def reset_cache(self) -> None:
        self._cache.clear(force=True)

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
        # Получаем текущий кэш используя ссылку как ключ
        response = self._cache[url]
        if not self._cache.validate(**request_args):
            response = await super(RequestManager, self).make_request(
                url=url,
                method=method,
                cookies=cookies,
                headers=headers,
                params=params,
                set_timeout=set_timeout,
                data=data,
                json=json,
            )
            if self.without_context:
                await self._close_session()
            self._cache_all(response, **request_args)
            return response
        return response.response_data  # type: ignore

    async def _close_session(self) -> None:
        return await super(RequestManager, self).close()

    async def close(self) -> None:
        """Close aiohttp session and reset cache data"""
        await super(RequestManager, self).close()
        self.reset_cache()

    def _cache_all(self, body: Any, **kwargs: Any) -> None:
        try:
            resolved = self._cache.convert_to_cache(result=body, kwargs=kwargs)
            self._cache[kwargs["url"]] = resolved
        except exceptions.InvalidCachePayload:
            pass

    @property
    def is_session_closed(self) -> bool:
        return (
            isinstance(self._session, aiohttp.ClientSession)  # noqa: W503
            and not self._session.closed  # noqa: W503
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
        result = await super().text_content(**prepared_payload)
        if self.without_context:
            await self._close_session()

        return result
