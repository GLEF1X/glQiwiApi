import asyncio
from itertools import repeat
from typing import Optional, Union, Dict, List, Tuple, Any, AsyncGenerator

from aiohttp import ClientTimeout, ClientSession, ClientRequest, ClientProxyConnectionError, \
    ServerDisconnectedError, ContentTypeError
from aiohttp.typedefs import LooseCookies
from aiosocksy import SocksError
from aiosocksy.connector import ProxyConnector, ProxyClientRequest

from glQiwiApi.abstracts import AbstractParser
from glQiwiApi.types import ProxyService, Response
from glQiwiApi.utils.exceptions import RequestProxyError

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
        return super().__getattribute__(item)

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


class HttpXParser(AbstractParser):
    """
    Представляет собой апи запросов для дальнейшего использования в запросах к разным
    платежным системам

    """
    _sleep_time = 2

    def __init__(self):
        self.base_headers = {
            'User-Agent': USER_AGENT,
            'Accept-Language': "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        self._core = Core()
        self.session: Optional[ClientSession] = None
        self.url = 'http://127.0.0.1/api/'
        self._timeout = ClientTimeout(total=5, connect=None, sock_connect=5, sock_read=None)
        self._connector: Optional[ProxyConnector] = None

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
            data: Optional[Dict[str, Union[str, int, List[Union[str, int]]]]] = None,
            headers: Optional[Dict[str, Union[str, int]]] = None,
            params: Optional[Dict[str, Union[str, int, List[Union[str, int]]]]] = None,
            **client_kwargs) -> Response:
        """
        Метод для отправки запроса,
        может возвращать в Response ProxyError в качестве response_data, это означает, что вы имеете проблемы с прокси,
        возможно нужно добавить дополнительные post данные, если вы используете method = POST, или headers,
        если запрос GET


        :param url: ссылка, куда вы хотите отправить ваш запрос
        :param get_json: указывает на то, хотите ли вы получить ответ в формате json
        :param method: Тип запроса(любой от обычного GET до PUT, DELETE)
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
        client_session_create_kwargs = {
            'timeout': self._timeout if set_timeout else DEFAULT_TIMEOUT,
            'connector': self._connector,
            'request_class': self.request_class if isinstance(proxy,
                                                              ProxyService) else ClientRequest,
            **client_kwargs
        }
        # Create new session if old was closed
        if not self.session:
            self.create_session(**client_session_create_kwargs)
        elif isinstance(self.session, ClientSession):
            if self.session.closed:
                self.create_session(**client_session_create_kwargs)

        # sending query
        try:
            response = await self.session.request(
                method=method,
                url=self.url if not url else url,
                data=data,
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

    def create_session(self, **kwargs) -> None:
        if not self.session:
            self.session = ClientSession(**kwargs)
        elif isinstance(self.session, ClientSession):
            if self.session.closed:
                self.session = ClientSession(**kwargs)

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
