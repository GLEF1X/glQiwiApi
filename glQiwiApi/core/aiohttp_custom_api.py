from typing import Dict, Optional, Any, Union, NoReturn

import aiohttp

from glQiwiApi.core.basic_requests_api import HttpXParser, _ProxyType
from glQiwiApi.core.storage import Storage
from glQiwiApi.types import Response
from glQiwiApi.types.basics import Cached, DEFAULT_CACHE_TIME
from glQiwiApi.utils.exceptions import RequestError


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
        super(RequestManager, self).__init__(proxy=proxy)

        self.without_context: bool = without_context
        self.messages: Optional[Dict[str, str]] = messages
        self._cache: Storage = Storage(cache_time=cache_time)

    def reset_cache(self) -> None:
        """ Clear all cache in storage """
        self._cache.clear(force=True)

    async def make_request(self, **kwargs) -> Response:
        """ The user-friendly method that allows sending requests to any URL  """
        return await super(RequestManager, self)._make_request(**kwargs)

    async def _make_request(self, *args, **kwargs) -> Response:
        """ Send request to service(API) """
        # Получаем текущий кэш используя ссылку как ключ
        response = self._cache[(kwargs.get('url'))]
        if not self._cache.validate(kwargs):
            try:
                response = await super()._make_request(*args, **kwargs)
            except aiohttp.ContentTypeError:
                raise RequestError(message="Unexpected error. Cannot deserialize answer.",
                                   status_code="unknown")

        # Проверяем, не был ли запрос в кэше, если нет,
        # то проверяем статус код и если он не 200 - выбрасываем ошибку
        if not isinstance(response, Cached):
            await self._close_session()
            if response.status_code != 200:
                self.raise_exception(
                    str(response.status_code),
                    json_info=response.response_data
                )

        self._cache_all(response, kwargs)

        return response

    async def _close_session(self):
        if self.without_context:
            await super(RequestManager, self).close()

    async def close(self) -> None:
        """ Close aiohttp session and reset cache data """
        await super(RequestManager, self).close()
        self.reset_cache()

    def raise_exception(
            self,
            status_code: str,
            json_info: Optional[Dict[str, Any]] = None,
            message: Optional[str] = None
    ) -> NoReturn:
        """ Raise RequestError exception with pretty explanation """
        if not isinstance(message, str):
            if self.messages is not None:
                message = self.messages.get(str(status_code), "Unknown")
        raise RequestError(
            message,
            status_code,
            additional_info=f"1.0.1 version api",
            json_info=json_info
        )

    def _cache_all(self, response: Response, kwargs: Dict[Any, Any]):
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
