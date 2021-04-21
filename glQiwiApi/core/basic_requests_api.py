import asyncio
import time
from itertools import repeat
from typing import (
    Dict,
    Tuple,
    AsyncGenerator
)
from typing import Optional, List, Any, Union

from aiohttp import (
    ClientTimeout,
    ClientRequest,
    ClientProxyConnectionError,
    ServerDisconnectedError,
    ContentTypeError,
    ClientSession
)
from aiohttp.typedefs import LooseCookies
from aiosocksy import SocksError
from aiosocksy.connector import ProxyConnector, ProxyClientRequest

from glQiwiApi.core import AbstractParser, BaseStorage
from glQiwiApi.types import ProxyService, Response
from glQiwiApi.types.basics import Cached, Attributes
from glQiwiApi.utils.exceptions import InvalidData

DEFAULT_TIMEOUT = ClientTimeout(total=5 * 60)

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
             '(KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'


class HttpXParser(AbstractParser):
    """
    Обвертка над aiohttp

    """

    _sleep_time = 2

    def __init__(self):
        super(HttpXParser, self).__init__()
        self.base_headers = {
            'User-Agent': USER_AGENT,
            'Accept-Language': "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        self._timeout = ClientTimeout(
            total=5,
            connect=None,
            sock_connect=5,
            sock_read=None
        )
        self._connector: Optional[ProxyConnector] = None
        self.request_class: Optional[
            Union[ClientRequest, ProxyClientRequest]
        ] = None

    async def _request(
            self,
            url: Optional[str] = None,
            get_json: bool = False,
            method: str = 'POST',
            set_timeout: bool = True,
            cookies: Optional[LooseCookies] = None,
            json: Optional[dict] = None,
            skip_exceptions: bool = False,
            proxy: Optional[ProxyService] = None,
            data: Optional[Dict[str, Union[
                str, int, List[
                    Union[str, int]
                ]]]
            ] = None,
            headers: Optional[Dict[str, Union[str, int]]] = None,
            params: Optional[
                Dict[str, Union[str, int, List[
                    Union[str, int]
                ]]]
            ] = None) -> Response:
        """
        Метод для отправки запроса,
        может возвращать в Response ProxyError в качестве response_data,
        это означает, что вы имеете проблемы с подключением к прокси,
        возможно нужно добавить дополнительные post данные,
        если вы используете method = POST, или headers,
        если запрос GET


        :param url: ссылка, куда вы хотите отправить ваш запрос
        :param get_json: указывает на то, хотите ли вы получить ответ
         в формате json
        :param method: Тип запроса
        :param proxy: instance of ProxyService
        :param data: payload data
        :param cookies:
        :param headers:
         aiohttp.ClientSession initialization
        :return: Response instance
        """
        headers = self.get_headers(headers)

        if isinstance(proxy, ProxyService):
            self._connector = ProxyConnector()
            self.request_class = ProxyClientRequest

        # Get "true" dict representation of ProxyService
        proxy_kwargs = proxy.get_proxy() \
            if isinstance(proxy, ProxyService) else {}

        # Create new session if old was closed
        self.create_session(
            timeout=self._timeout if set_timeout else DEFAULT_TIMEOUT,
            connector=self._connector,
            request_class=self.request_class if isinstance(
                proxy, ProxyService
            ) else ClientRequest
        )

        # sending query to some endpoint url
        try:
            response = await self.session.request(
                method=method,
                url=url,
                data=data,
                headers=headers,
                json=json if isinstance(json, dict) else None,
                cookies=cookies,
                params=params,
                **proxy_kwargs
            )
        except (
                ClientProxyConnectionError,
                SocksError,
                ServerDisconnectedError
        ) as ex:
            if not skip_exceptions:
                self.raise_exception(
                    status_code='400_special_bad_proxy',
                    json_info=ex
                )
            return Response.bad_response()
        # Get content and return response
        try:
            data = await response.json(
                content_type="application/json"
            )
        except ContentTypeError:
            if get_json:
                return Response(status_code=response.status)
            data = await response.read()
        return Response(
            status_code=response.status,
            response_data=data,
            raw_headers=response.raw_headers,
            cookies=response.cookies,
            ok=response.ok,
            content_type=response.content_type,
            host=response.host,
            url=response.url.__str__()
        )

    def get_headers(self, headers: Optional[dict]) -> Optional[dict]:
        if isinstance(headers, dict):
            return headers
        return self.base_headers

    async def fetch(
            self,
            *,
            times: int = 1,
            **kwargs
    ) -> AsyncGenerator[Response, None]:
        """
        Basic usage: \n
        parser = HttpXParser() \n
        async for response in parser.fetch():
            print(response)

        :param times: int of quantity requests
        :param kwargs: HttpXParser._request kwargs
        :return:
        """
        coroutines = [self._request(**kwargs) for _ in repeat(None, times)]
        for future in asyncio.as_completed(fs=coroutines):
            yield await future

    def fast(self) -> 'HttpXParser':
        """
        Method to fetching faster with using faster event loop(uvloop) \n
        USE IT ONLY ON LINUX SYSTEMS,
        on Windows or Mac its dont give performance!

        :return:
        """
        try:
            from uvloop import EventLoopPolicy
            asyncio.set_event_loop_policy(EventLoopPolicy())
        except ImportError:
            # Catching import error and forsake standard policy
            from asyncio import DefaultEventLoopPolicy as EventLoopPolicy
            asyncio.set_event_loop_policy(EventLoopPolicy())
        return self

    @staticmethod
    def combine_proxies(
            proxies: Union[List[ProxyService], Tuple[ProxyService]]
    ) -> Union[
        List[ProxyService], Tuple[ProxyService]
    ]:
        """
        Method to combine proxies

        :param proxies:
        :return: shuffled iterable(list or tuple of CredentialService objects)
        """
        import random
        random.shuffle(proxies)
        return proxies


class Storage(BaseStorage):
    """
    Класс, позволяющий кэшировать результаты запросов

    """
    # Доступные критерии, по которым проходит валидацию кэш
    available = ('params', 'json', 'data', 'headers')

    def __init__(
            self,
            cache_time: Union[float, int],
            default_key: Optional[str] = None
    ) -> None:
        if isinstance(cache_time, (int, float)):
            if cache_time > 60 or cache_time < 0:
                raise InvalidData(
                    "Время кэширования должно быть в пределах"
                    " от 0 до 60 секунд"
                )

        self.tmp_data: Optional[Dict[str, Cached]] = dict()
        self._cache_time = cache_time
        self.__initialize_default_key(default_key)

    def __del__(self) -> None:
        del self.tmp_data

    def __initialize_default_key(self, key: str) -> None:
        """ Initialize default_key attribute """
        self._default_key = key
        if not isinstance(key, str):
            self._default_key = "url"

    def get_current(self, key: str) -> Optional[Cached]:
        """ Method to get element by key from data """
        return self.tmp_data.get(key)

    def clear(self, key: Optional[str] = None, force: bool = False) -> Any:
        """
        Method to delete element from the cache by key,
        or if force passed on its clear all data from the cache

        """
        if force:
            return self.tmp_data.clear()
        return self.tmp_data.pop(key)

    def __setitem__(self, key, value) -> None:
        self.tmp_data.update(
            {key: value}
        )

    def __getitem__(self, item) -> Union[
        Cached, ClientSession
    ]:
        return self.tmp_data.get(item)

    def update_data(
            self,
            result: Any,
            kwargs: Any,
            status_code: Optional[Union[str, int]] = None
    ) -> None:
        """
        Метод, который добавляет результат запроса в кэш

        :param result: Результат запроса или какие-то данные
        :param kwargs: Дополнительная информация
        :param status_code: опционально, статус код запроса

        """
        uncached = (
            'https://api.qiwi.com/partner/bill', '/sinap/api/v2/terms/'
        )
        value = kwargs.get(self._default_key)
        if not self._cache_time < 0.1:
            if not any(
                    value.startswith(
                        contain_match
                    ) or contain_match in value
                    for contain_match in uncached
            ):
                self.tmp_data.update({
                    value: Cached(
                        kwargs=Attributes.format(kwargs, self.available),
                        response_data=result,
                        key=self._default_key,
                        status_code=status_code,
                        method=kwargs.get('method')
                    )
                })
            elif uncached[1] in value:
                self.clear(value, True)

    def validate(self, kwargs: Dict[str, Any]) -> bool:
        """
        Метод, который по некоторым условиям
        проверяет актуальность кэша и в некоторых
        случая его чистит.

        """
        # Если параметры и ссылка запроса совпадает
        cached = self.tmp_data.get(kwargs.get(self._default_key))
        if isinstance(cached, Cached):
            # Проверяем, не вышло ли время кэша
            if time.monotonic() - cached.cached_in > self._cache_time:
                self.clear(kwargs.get(self._default_key))
                return False

            # Проверяем запрос методом GET на кэш
            if cached.method == 'GET':
                if kwargs.get('headers') == cached.kwargs.headers:
                    if kwargs.get('params') == cached.kwargs.params:
                        return True

            elif any(
                    getattr(cached.kwargs, key) == kwargs.get(key, '')
                    for key in self.available if key != 'headers'
            ):
                return True

        return False
