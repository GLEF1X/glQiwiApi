from asyncio import as_completed, set_event_loop_policy
from itertools import repeat
from typing import (
    Dict,
    AsyncGenerator,
    NoReturn
)
from typing import Optional, List, Union

from aiohttp import (
    ClientTimeout,
    ClientProxyConnectionError,
    ServerDisconnectedError,
    ContentTypeError
)
from aiohttp.typedefs import LooseCookies

from glQiwiApi.core import AbstractParser
from glQiwiApi.types import Response
from glQiwiApi.types.basics import Cached

DEFAULT_TIMEOUT = ClientTimeout(total=5 * 60)

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
             '(KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'


class HttpXParser(AbstractParser):
    """
    Обвертка над aiohttp

    """

    _sleep_time = 2

    def __init__(self) -> NoReturn:
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

    async def _request(
            self,
            url: Optional[str] = None,
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
        :param data: payload data
        :param cookies:
        :param headers:
         aiohttp.ClientSession initialization
        :return: Response instance
        """
        headers = self.get_headers(headers)
        # Create new session if old was closed
        self.create_session(
            timeout=self._timeout if set_timeout else DEFAULT_TIMEOUT
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
            )
        except (
                ClientProxyConnectionError,
                ServerDisconnectedError
        ) as ex:
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
    ) -> AsyncGenerator[Union[Response, Cached], None]:
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
        for future in as_completed(fs=coroutines):
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
            set_event_loop_policy(EventLoopPolicy())
        except ImportError:
            # Catching import error and forsake standard policy
            from asyncio import DefaultEventLoopPolicy as EventLoopPolicy
            set_event_loop_policy(EventLoopPolicy())
        return self
