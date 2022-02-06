import functools
import inspect
import sys
from asyncio import Transport
from typing import Any, Mapping, Tuple, Type, TypeVar, cast, no_type_check

from aiohttp import web
from aiohttp.abc import AbstractView
from aiohttp.web_request import Request

from glQiwiApi.core.event_fetching.webhooks.services.security.ip import IPFilter


def check_ip(ip_filter: IPFilter, request: web.Request) -> Tuple[str, bool]:
    # Try to resolve client IP over reverse proxy
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        forwarded_for, *_ = forwarded_for.split(",", maxsplit=1)
        return forwarded_for, forwarded_for in ip_filter

    peer_name = cast(Transport, request.transport).get_extra_info("peername")
    # When reverse proxy is not configured IP address can be resolved from incoming connection
    if peer_name:
        host, _ = peer_name
        return host, host in ip_filter

    # Potentially impossible case
    return "", False  # pragma: no cover


View = TypeVar("View", bound=Type[AbstractView])


def inject_dependencies(view: View, dependencies: Mapping[str, Any]) -> View:
    params = inspect.signature(view.__init__).parameters

    deps = {
        name: dependency
        for name, dependency in dependencies.items()
        if not isinstance(dependency, (Request, AbstractView)) and name in params
    }

    return cast(View, partial_class(view.__qualname__, view, **deps))  # type: ignore


@no_type_check
def partial_class(name, cls, *args, **kwds):
    new_cls = type(
        name, (cls,), {"__init__": functools.partialmethod(cls.__init__, *args, **kwds)}
    )

    # The following is copied nearly ad verbatim from `namedtuple's` source.
    """
    # For pickling to work, the __module__ variable needs to be set to the frame
    # where the named tuple is created.  Bypass this step in enviroments where
    # sys._getframe is not defined (Jython for example) or sys._getframe is not
    # defined for arguments greater than 0 (IronPython).
    """
    try:
        new_cls.__module__ = sys._getframe(1).f_globals.get("__name__", "__main__")  # noqa
    except (AttributeError, ValueError):  # pragma: no cover
        pass

    return new_cls
