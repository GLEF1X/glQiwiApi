import asyncio
from itertools import repeat
from typing import Literal, Optional, Union, Dict, List, Tuple, Any, Type, AsyncGenerator

from aiohttp import ClientTimeout, ClientSession, ContentTypeError, ClientRequest, ClientProxyConnectionError, \
    ServerDisconnectedError
from aiohttp.typedefs import LooseCookies
from aiosocksy import SocksError
from aiosocksy.connector import ProxyConnector, ProxyClientRequest

from glQiwiApi.data import ProxyService, Response
from glQiwiApi.exceptions import RequestProxyError, RequestAuthError

DEFAULT_TIMEOUT = ClientTimeout(total=5 * 60)
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'


class Core:
    """
    Class, which include some help methods to HttpXParser

    """

    def __getattr__(self, item: Any) -> Any:
        """
        Method, which can get an attribute of base_headers by this method

        :param item: key name of base_headers dict data
        :return:
        """
        try:
            return self.base_headers.get(item)
        except KeyError:
            """Returning None"""

    def __eq__(self, other: Any) -> bool:
        """
        Method to compare instances of parsers

        :param other: other object
        :return: bool
        """
        if isinstance(other, HttpXParser):
            if other.url == self.url and other.base_headers == self.base_headers:
                return True
        return False

    def __setitem__(self, key, value) -> None:
        """

        :param key: key of base_headers dict
        :param value: value of base_headers dict
        :return: None
        """
        self.base_headers.update(
            {key: value}
        )


class HttpXParser:
    """
    Представляет собой апи, для парсинга сайта с определенными изменениями и плюшками

    """
    _sleep_time = 2

    def __init__(self):
        self.base_headers = {
            'User-Agent': USER_AGENT,
            'Accept-Language': "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        self._core = Core()
        self._session: Optional[ClientSession] = None
        self.url = 'http://127.0.0.1/api/'
        self._timeout = ClientTimeout(total=2 * 15, connect=None, sock_connect=5, sock_read=None)
        self._connector: Optional[ProxyConnector] = None

    async def _request(
            self,
            url: Optional[str] = None,
            get_json: bool = False,
            validate_django: bool = False,
            method: Literal['POST', 'GET', 'PUT'] = 'POST',
            set_timeout: bool = True,
            cookies: Optional[LooseCookies] = None,
            json: Optional[dict] = None,
            skip_exceptions: bool = False,
            proxy: Optional[ProxyService] = None,
            data: Optional[Dict[str, Union[str, int, List[Union[str, int]]]]] = None,
            headers: Optional[Dict[str, Union[str, int]]] = None,
            params: Optional[Dict[str, Union[str, int, List[Union[str, int]]]]] = None,
            session: Optional[Type[ClientSession]] = None,
            **client_kwargs) -> Response:
        """
        Метод для отправки запроса,
        может возвращать в Response ProxyError в качестве response_data, это означает, что вы имеете проблемы с прокси,
        возможно нужно добавить дополнительные post данные, если вы используете method = POST, или headers,
        если запрос GET


        :param url: ссылка, куда вы хотите отправить ваш запрос
        :param get_json: указывает на то, хотите ли вы получить ответ в формате json
        :param method: POST or GET(тип запроса)
        :param proxy: instance of ProxyService
        :param data: post data
        :param cookies:
        :param headers:
        :param session: aiohttp.ClientSession object
        :param client_kwargs: key/value for aiohttp.ClientSession initialization
        :return: Response instance
        """
        headers = headers if isinstance(headers, dict) else self.base_headers

        if isinstance(proxy, ProxyService):
            self._connector = ProxyConnector()
            self.request_class = ProxyClientRequest

        try:
            proxy_kwargs = proxy.get_proxy()
        except AttributeError:
            proxy_kwargs = {}

        if not isinstance(session, ClientSession):
            # Sending query
            async with ClientSession(
                    timeout=self._timeout if set_timeout else DEFAULT_TIMEOUT,
                    connector=self._connector,
                    request_class=self.request_class if isinstance(proxy, ProxyService) else ClientRequest,
                    **client_kwargs
            ) as session:
                self._session = session
                try:
                    response = await self._session.request(
                        method=method,
                        url=self.url if not url else url,
                        data=self._set_auth(data) if validate_django else data,
                        headers=headers,
                        json=json if isinstance(json, dict) else None,
                        cookies=cookies,
                        params=params,
                        **proxy_kwargs
                    )
                except (ClientProxyConnectionError, SocksError, ServerDisconnectedError) as ex:
                    if not skip_exceptions:
                        raise ConnectionError() from ex
                    return Response.bad_response()
                # Get content from site
                try:
                    data = await response.json(
                        content_type="application/json"
                    )
                except ContentTypeError as ex:
                    if get_json:
                        raise RequestAuthError() from ex
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

    @staticmethod
    def _set_auth(
            data: Optional[
                Dict[str, Union[str, int, List[Union[str, int]], Tuple[Union[str, int]]]]
            ] = None) -> Optional[Dict[str, str]]:
        """
        Метод валидации для джанго апи

        :param data: It must be dict(your headers or data)
        :return: validated data or headers
        """
        try:
            from djangoProject.settings import SECRET_KEY, SECRET_CODE
        except ImportError:
            SECRET_KEY = None
            SECRET_CODE = None
        if not isinstance(data, dict):
            data = {}
        data.update(
            {
                'SECRET_KEY': SECRET_KEY,
                'SECRET_CODE': SECRET_CODE
            }
        )
        return data

    async def fetch(self, *, times: int = 1, **kwargs) -> AsyncGenerator[Response, None]:
        """
        Basic usage: \n
        parser = HttpXParser() \n
        async for response in parser.fetch():
            print(response)

        :param times: int of quantity requests
        :param kwargs: HttpXParser._request kwargs
        :return:
        """
        try:
            django_support = kwargs.get('validate_django')
            if django_support and kwargs.get('proxy'):
                raise RequestProxyError('Invalid params. You cant use proxy with django localhost')
        except KeyError:
            pass
        coroutines = [self._request(**kwargs) for _ in repeat(None, times)]
        for future in asyncio.as_completed(fs=coroutines):
            yield await future

    def fast(self) -> 'HttpXParser':
        """
        Method to fetching faster with using faster event loop(uvloop) \n
        USE IT ONLY ON LINUX SYSTEMS, on windows or mac its dont give performance!

        :return:
        """
        try:
            from uvloop import EventLoopPolicy
            asyncio.set_event_loop_policy(EventLoopPolicy())
        except ImportError:
            "Catching import error and forsake standard policy"
            from asyncio import DefaultEventLoopPolicy as EventLoopPolicy
            asyncio.set_event_loop_policy(EventLoopPolicy())
        return self

    def __getattr__(self, item: Any) -> Any:
        """
        Method, which can get an attribute of base_headers by this method

        :param item: key name of base_headers dict data
        :return:
        """
        return self._core.__getattr__(item)

    def __eq__(self, other: Any) -> bool:
        """
        Method to compare instances of parsers

        :param other: other object
        :return: bool
        """
        return self._core.__eq__(other)

    def __setitem__(self, key, value) -> None:
        """

        :param key: key of base_headers dict
        :param value: value of base_headers dict
        :return: None
        """
        self._core.__setitem__(key, value)

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
