from typing import Dict, Optional, Any, Union, NoReturn

import aiohttp

from glQiwiApi.core.basic_requests_api import HttpXParser, _ProxyType
from glQiwiApi.core.storage import Storage
from glQiwiApi.types import Response
from glQiwiApi.types.basics import Cached, DEFAULT_CACHE_TIME
from glQiwiApi.utils.exceptions import RequestError


class RequestManager(HttpXParser):
    """
    Немного переделанный HttpXParser
    под платежные системы и кэширование запросов

    """
    __slots__ = (
        'without_context', 'messages', '_cache', '_cached_key',
        '_connector_type', '_connector_init', '_should_reset_connector',
        '_proxy'
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
        self._cached_key: str = "session"

    def reset_storage(self) -> None:
        """ Clear all cache in storage """
        self._cache.clear(force=True)

    async def _request(self, *args, **kwargs) -> Response:
        # Получаем текущий кэш используя ссылку как ключ
        response = self._cache[(kwargs.get('url'))]
        if not self._cache.validate(kwargs):
            response = await super()._request(*args, **kwargs)
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
            additional_info=f"0.2.23 version api",
            json_info=json_info
        )

    async def _close_session(self):
        if self.without_context and not self.session.closed:
            await self.session.close()

    def _cache_all(self, response: Response, kwargs: Dict[Any, Any]):
        resolved: Cached = self._cache.convert_to_cache(
            result=response.response_data,
            kwargs=kwargs,
            status_code=response.status_code
        )
        self._cache[kwargs["url"]] = resolved

    @property
    def is_session_closed(self) -> bool:
        if isinstance(self.session, aiohttp.ClientSession):
            if not self.session.closed:
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
