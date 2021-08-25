from __future__ import annotations

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
from glQiwiApi.utils.exceptions import APIError
from glQiwiApi.utils.payload import check_result

_ProxyBasic = Union[str, Tuple[str, aiohttp.BasicAuth]]
_ProxyChain = Iterable[_ProxyBasic]
_ProxyType = Union[_ProxyChain, _ProxyBasic]


def _retrieve_basic(basic: _ProxyBasic) -> Dict[str, Any]:
    from aiohttp_socks.utils import parse_proxy_url

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
    from aiohttp_socks import ChainProxyConnector, ProxyConnector, ProxyInfo

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


class EmptyMessages(Dict[Any, Any]):
    EMPTY_STRING = ""

    def __init__(self) -> None:
        super().__init__({})

    def __getattr__(self, item: Any) -> Any:
        return self.EMPTY_STRING


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
        self.messages = messages or EmptyMessages()
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
        **kwargs: Any,
    ) -> Dict[Any, Any]:
        headers = headers or self.base_headers
        session = await self.create_session(
            timeout=self._timeout if set_timeout else DEFAULT_TIMEOUT
        )
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

    async def create_session(self, **kwargs: Any) -> aiohttp.ClientSession:
        """Creating new session if old was close or it's None"""
        if self.proxy is not None:
            kwargs.update(connector=self._connector_type(**self._connector_init))

        if self._should_reset_connector and isinstance(self._session, ClientSession):
            await self._session.close()

        if (
            isinstance(self._session, ClientSession)
            and self._session.closed  # noqa: W503
            or not isinstance(self._session, ClientSession)  # noqa: W503
        ):
            self._session = ClientSession(**kwargs)
            self._should_reset_connector = False
        return self._session

    async def close(self) -> None:
        """close aiohttp session"""
        if isinstance(self._session, ClientSession) and not self._session.closed:
            await self._session.close()

    async def retrieve_bytes(self, url: str, method: str, **kwargs: Any) -> bytes:
        session = await self.create_session()
        resp = await session.request(method, url, **kwargs)
        return await resp.read()

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
        headers = headers or self.base_headers
        timeout = self._timeout if set_timeout else DEFAULT_TIMEOUT
        session = await self.create_session(timeout=timeout)
        resp = await session.request(
            method=method,
            url=url,
            data=data,
            headers=headers,
            json=json if isinstance(json, dict) else None,
            cookies=cookies,
            params=params,
        )
        return await resp.text(encoding=encoding)
