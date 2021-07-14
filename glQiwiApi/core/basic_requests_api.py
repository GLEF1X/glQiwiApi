from __future__ import annotations

from asyncio import set_event_loop_policy
from typing import Dict, Optional, Any, Union, Tuple, Type, Iterable, cast, List

import aiohttp
from aiohttp import (
    ClientTimeout,
    ClientProxyConnectionError,
    ServerDisconnectedError,
    ClientConnectionError,
    ClientSession,
)
from aiohttp.typedefs import LooseCookies

from glQiwiApi.core import AbstractParser
from glQiwiApi.core.constants import DEFAULT_TIMEOUT
from glQiwiApi.utils.api_helper import check_result
from glQiwiApi.utils.errors import RequestError

_ProxyBasic = Union[str, Tuple[str, aiohttp.BasicAuth]]
_ProxyChain = Iterable[_ProxyBasic]
_ProxyType = Union[_ProxyChain, _ProxyBasic]


def _retrieve_basic(basic: _ProxyBasic) -> Dict[str, Any]:
    from aiohttp_socks.utils import parse_proxy_url  # type: ignore

    proxy_auth: Optional[aiohttp.BasicAuth] = None

    if isinstance(basic, str):
        proxy_url = basic
    else:
        proxy_url, proxy_auth = basic

    proxy_type, host, port, username, password = parse_proxy_url(proxy_url)
    if isinstance(proxy_auth, aiohttp.BasicAuth):
        username = proxy_auth.login
        password = proxy_auth.password

    return dict(
        proxy_type=proxy_type,
        host=host,
        port=port,
        username=username,
        password=password,
        rdns=True,
    )


def _prepare_connector(
    chain_or_plain: _ProxyType,
) -> Tuple[Type["aiohttp.TCPConnector"], Dict[str, Any]]:
    from aiohttp_socks import ChainProxyConnector, ProxyConnector, ProxyInfo  # type: ignore

    # since tuple is Iterable(compatible with _ProxyChain) object, we assume that
    # user wants chained proxies if tuple is a pair of string(url) and BasicAuth
    if isinstance(chain_or_plain, str) or (
        isinstance(chain_or_plain, tuple) and len(chain_or_plain) == 2
    ):
        chain_or_plain = cast(_ProxyBasic, chain_or_plain)
        return ProxyConnector, _retrieve_basic(chain_or_plain)

    chain_or_plain = cast(_ProxyChain, chain_or_plain)
    infos: List[ProxyInfo] = []
    for basic in chain_or_plain:
        infos.append(ProxyInfo(**_retrieve_basic(basic)))

    return ChainProxyConnector, dict(proxy_infos=infos)


class HttpXParser(AbstractParser):
    """
    Aiohttp wrapper, implements the method of sending a request

    """

    def __init__(
        self,
        proxy: Optional[_ProxyType] = None,
        messages: Optional[Dict[int, str]] = None,
    ) -> None:
        self.base_headers = {
            "User-Agent": "glQiwiApi/1.0beta",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        self.messages = messages
        self._timeout = ClientTimeout(
            total=5, connect=None, sock_connect=5, sock_read=None
        )
        self._session: Optional[ClientSession] = None
        self._connector_type: Type[aiohttp.TCPConnector] = aiohttp.TCPConnector
        self._connector_init: Dict[str, Any] = {}
        self._should_reset_connector = False  # flag determines connector state
        self._proxy: Optional[_ProxyType] = None

        if proxy is not None:
            try:
                self._setup_proxy_connector(proxy)
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError(
                    "In order to use aiohttp client for proxy requests, install "
                    "https://pypi.org/project/aiohttp-socks/"
                ) from exc

    def _setup_proxy_connector(self, proxy: _ProxyType) -> None:
        self._connector_type, self._connector_init = _prepare_connector(proxy)
        self._proxy = proxy

    @property
    def proxy(self) -> Optional[_ProxyType]:
        return self._proxy

    @proxy.setter
    def proxy(self, proxy: _ProxyType) -> None:
        self._setup_proxy_connector(proxy)
        self._should_reset_connector = True

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
        **kwargs,
    ) -> Dict[Any, Any]:
        """
        Send request to some url. Method has a similar signature with the `aiohttp.request`


        :param url: ссылка, куда вы хотите отправить ваш запрос
        :param method: Тип запроса
        :param data: payload data
        :param set_timeout:
        :param json:
        :param cookies: куки запроса
        :param headers: заголовки запроса
        :param params:
        :param kwargs:
        :return: Response instance
        """
        headers = headers or self.base_headers
        # Create new session if old was closed
        session = await self.create_session(
            timeout=self._timeout if set_timeout else DEFAULT_TIMEOUT
        )

        # sending query to some endpoint url
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
            return check_result(
                self.messages,
                resp.content_type,
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

    def fast(self) -> HttpXParser:
        """
        Method to fetching faster with using faster event loop(uvloop) \n
        USE IT ONLY ON LINUX SYSTEMS,
        on Windows or Mac its dont give performance!

        :return:
        """
        try:
            from uvloop import EventLoopPolicy  # type: ignore

            set_event_loop_policy(EventLoopPolicy())
        except ImportError:
            # Catching import error and forsake standard policy
            from asyncio import DefaultEventLoopPolicy as EventLoopPolicy  # type: ignore

            set_event_loop_policy(EventLoopPolicy())
        return self

    async def create_session(self, **kwargs) -> aiohttp.ClientSession:
        """ Creating new session if old was close or it's None """
        if self.proxy is not None:
            kwargs.update(connector=self._connector_type(**self._connector_init))

        if self._should_reset_connector and isinstance(self._session, ClientSession):
            await self._session.close()

        if not isinstance(self._session, ClientSession):
            self._session = ClientSession(**kwargs)
            self._should_reset_connector = False
        elif isinstance(self._session, ClientSession):
            if self._session.closed:
                self._session = ClientSession(**kwargs)
                self._should_reset_connector = False
        return self._session

    async def close(self) -> None:
        """ close aiohttp session"""
        if isinstance(self._session, ClientSession):
            if not self._session.closed:
                await self._session.close()

    async def stream_content(self, url: str, method: str, **kwargs) -> bytes:
        session = await self.create_session()
        resp = await session.request(method, url, **kwargs)
        return await resp.read()

    def make_exception(
        self,
        status_code: int,
        traceback_info: Optional[Union[aiohttp.RequestInfo, dict, str, bytes]] = None,
        message: Optional[str] = None,
    ) -> RequestError:
        """ Raise :class:`RequestError` exception with pretty explanation """
        from glQiwiApi import __version__

        if not isinstance(message, str):
            if isinstance(self.messages, dict):
                message = self.messages.get(status_code, "Unknown")  # type: ignore
        return RequestError(
            message,
            status_code,
            additional_info=f"{__version__} version api",
            traceback_info=traceback_info,
        )

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
        **kwargs,
    ):
        headers = headers or self.base_headers
        # Create new session if old was closed
        session = await self.create_session(
            timeout=self._timeout if set_timeout else DEFAULT_TIMEOUT
        )
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
        return await resp.text(encoding=encoding)
