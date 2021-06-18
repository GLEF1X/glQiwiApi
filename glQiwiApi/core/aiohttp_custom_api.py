from typing import Dict, Optional, Any, Union, List

import aiohttp
from aiohttp.typedefs import LooseCookies

from glQiwiApi.core.basic_requests_api import HttpXParser, _ProxyType
from glQiwiApi.core.storage import Storage
from glQiwiApi.types import Response
from glQiwiApi.types.basics import Cached, DEFAULT_CACHE_TIME


class RequestManager(HttpXParser):
    """
    Deal with :class:`Storage`,
    caching queries and managing stable work of sending requests

    """
    __slots__ = (
        'without_context', 'messages', '_cache', '_should_reset_connector',
        '_connector_type', '_connector_init', '_proxy'
    )

    def __init__(
            self,
            without_context: bool = False,
            messages: Optional[Dict[str, str]] = None,
            cache_time: Union[float, int] = DEFAULT_CACHE_TIME,
            proxy: Optional[_ProxyType] = None
    ) -> None:
        super(RequestManager, self).__init__(proxy=proxy, messages=messages)

        self.without_context: bool = without_context
        self._cache: Storage = Storage(cache_time=cache_time)

    def reset_cache(self) -> None:
        """ Clear all cache in storage """
        self._cache.clear(force=True)

    async def make_request(self, **kwargs) -> Union[Response, Cached]:
        """ The user-friendly method that allows sending requests to any URL  """
        return await super(RequestManager, self)._make_request(**kwargs)

    async def _make_request(self,
                            url: str,
                            get_json: bool = False,
                            method: str = 'POST',
                            set_timeout: bool = True,
                            cookies: Optional[LooseCookies] = None,
                            json: Optional[dict] = None,
                            data: Optional[Dict[str, Union[
                                str, int, List[
                                    Union[str, int]
                                ]]]
                            ] = None,
                            headers: Optional[dict] = None,
                            params: Optional[
                                Dict[str, Union[str, int, List[
                                    Union[str, int]
                                ]]]
                            ] = None,
                            get_bytes: bool = False,
                            **kwargs) -> Union[Response, Cached]:
        """ Send request to service(API) """
        request_args = {k: v for k, v in locals().items() if not isinstance(v, type(self))}
        # Получаем текущий кэш используя ссылку как ключ
        response: Optional[Any] = self._cache[url]
        if not self._cache.validate(**request_args):
            response = await super()._make_request(
                url=url,
                method=method,
                get_json=get_json,
                get_bytes=get_bytes,
                cookies=cookies,
                headers=headers,
                params=params,
                set_timeout=set_timeout,
                data=data,
                json=json
            )
        # Проверяем, не был ли запрос в кэше, если нет,
        # то проверяем статус код и если он не 200 - выбрасываем ошибку
        if not isinstance(response, Cached) and isinstance(response, Response):
            if self.without_context:
                await self._close_session()
            if response.status_code != 200:
                raise self.make_exception(
                    response.status_code,
                    traceback_info=response.response_data
                )
            else:
                self._cache_all(response, **request_args)

        return response

    async def _close_session(self):
        await super(RequestManager, self).close()

    async def close(self) -> None:
        """ Close aiohttp session and reset cache data """
        await super(RequestManager, self).close()
        self.reset_cache()

    def _cache_all(self, response: Response, **kwargs: Any):
        resolved: Cached = self._cache.convert_to_cache(
            result=response.response_data,
            kwargs=kwargs,
            status_code=response.status_code
        )
        self._cache[kwargs["url"]] = resolved

    @property
    def is_session_closed(self) -> bool:
        if isinstance(self._session, aiohttp.ClientSession):
            if not self._session.closed:
                return True
        return False

    @classmethod
    def filter_dict(cls, dictionary: dict) -> dict:
        """
        Pop NoneType values and convert everything to str, designed?for=params

        :param dictionary: source dict
        :return: filtered dict
        """
        return {k: str(v) for k, v in dictionary.items() if v is not None}
