import logging
from typing import Any, Awaitable, Callable

from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp.web_middlewares import middleware

from glQiwiApi.core.event_fetching.webhooks.services.security.ip import IPFilter
from glQiwiApi.core.event_fetching.webhooks.utils import check_ip

logger = logging.getLogger("glQiwiApi.webhooks.middlewares")


def ip_filter_middleware(ip_filter: IPFilter) -> Callable[[web.Request, Handler], Awaitable[Any]]:
    @middleware
    async def _ip_filter_middleware(request: web.Request, handler: Handler) -> Any:
        ip_address, accept = check_ip(ip_filter=ip_filter, request=request)
        if not accept:
            logger.warning(f"Blocking request from an unauthorized IP: {ip_address}")
            raise web.HTTPUnauthorized()
        return await handler(request)

    return _ip_filter_middleware
