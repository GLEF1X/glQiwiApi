import aiohttp
from aiohttp.client_exceptions import (
    ServerFingerprintMismatch,
    ssl_errors
)
try:
    from aiohttp.client_exceptions import certificate_errors
except ImportError:
    from aiohttp.client_exceptions import cert_errors as certificate_errors

from .errors import SocksConnectionError
from .helpers import Socks4Auth, Socks5Auth, Socks4Addr, Socks5Addr
from . import create_connection

__all__ = ('ProxyConnector', 'ProxyClientRequest')


from distutils.version import StrictVersion

if StrictVersion(aiohttp.__version__) < StrictVersion('3.0'):
    raise RuntimeError(
        'aiosocksy.connector depends on aiohttp 3.0+'
    )  # pragma: no cover


class ProxyClientRequest(aiohttp.ClientRequest):
    def update_proxy(self, proxy, proxy_auth, proxy_headers):
        if proxy and proxy.scheme not in ['http', 'socks4', 'socks5']:
            raise ValueError(
                "Only http, socks4 and socks5 proxies are supported")
        if proxy and proxy_auth:
            if proxy.scheme == 'http' and \
                    not isinstance(proxy_auth, aiohttp.BasicAuth):
                raise ValueError("proxy_auth must be None or "
                                 "BasicAuth() tuple for http proxy")
            if proxy.scheme == 'socks4' and \
                    not isinstance(proxy_auth, Socks4Auth):
                raise ValueError("proxy_auth must be None or Socks4Auth() "
                                 "tuple for socks4 proxy")
            if proxy.scheme == 'socks5' and \
                    not isinstance(proxy_auth, Socks5Auth):
                raise ValueError("proxy_auth must be None or Socks5Auth() "
                                 "tuple for socks5 proxy")
        self.proxy = proxy
        self.proxy_auth = proxy_auth
        self.proxy_headers = proxy_headers


class ProxyConnector(aiohttp.TCPConnector):
    def __init__(self, remote_resolve=True, **kwargs):
        super().__init__(**kwargs)

        self._remote_resolve = remote_resolve

    async def _create_proxy_connection(self, req, *args, **kwargs):
        """
        args, kwargs can contain different elements (traces, timeout,...)
        depending on aiohttp version
        """
        if req.proxy.scheme == 'http':
            return await super()._create_proxy_connection(req, *args, **kwargs)
        else:
            return await self._create_socks_connection(req=req)

    async def _wrap_create_socks_connection(self, *args, req, **kwargs):
        try:
            return await create_connection(*args, **kwargs)
        except certificate_errors as exc:
            raise aiohttp.ClientConnectorCertificateError(
                req.connection_key, exc) from exc
        except ssl_errors as exc:
            raise aiohttp.ClientConnectorSSLError(
                req.connection_key, exc) from exc
        except (OSError, SocksConnectionError) as exc:
            raise aiohttp.ClientProxyConnectionError(
                req.connection_key, exc) from exc

    async def _create_socks_connection(self, req):
        sslcontext = self._get_ssl_context(req)
        fingerprint = self._get_fingerprint(req)

        if not self._remote_resolve:
            try:
                dst_hosts = list(await self._resolve_host(
                    req.host, req.port))
                dst = dst_hosts[0]['host'], dst_hosts[0]['port']
            except OSError as exc:
                raise aiohttp.ClientConnectorError(
                    req.connection_key, exc) from exc
        else:
            dst = req.host, req.port

        try:
            proxy_hosts = await self._resolve_host(
                req.proxy.host, req.proxy.port)
        except OSError as exc:
            raise aiohttp.ClientConnectorError(
                req.connection_key, exc) from exc

        last_exc = None

        for hinfo in proxy_hosts:
            if req.proxy.scheme == 'socks4':
                proxy = Socks4Addr(hinfo['host'], hinfo['port'])
            else:
                proxy = Socks5Addr(hinfo['host'], hinfo['port'])

            try:
                transp, proto = await self._wrap_create_socks_connection(
                    self._factory, proxy, req.proxy_auth, dst,
                    loop=self._loop, remote_resolve=self._remote_resolve,
                    ssl=sslcontext, family=hinfo['family'],
                    proto=hinfo['proto'], flags=hinfo['flags'],
                    local_addr=self._local_addr, req=req,
                    server_hostname=req.host if sslcontext else None)
            except aiohttp.ClientConnectorError as exc:
                last_exc = exc
                continue

            if req.is_ssl() and fingerprint:
                try:
                    fingerprint.check(transp)
                except ServerFingerprintMismatch as exc:
                    transp.close()
                    if not self._cleanup_closed_disabled:
                        self._cleanup_closed_transports.append(transp)
                    last_exc = exc
                    continue

            return transp, proto
        else:
            raise last_exc
