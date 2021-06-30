from dataclasses import dataclass
from http.cookies import SimpleCookie
from typing import Optional, Any

from aiohttp.typedefs import RawHeaders

from glQiwiApi.utils.errors import NetworkError


@dataclass
class Response:
    """ object: Response """

    status_code: int
    response_data: Any
    url: Optional[str] = None
    raw_headers: Optional[RawHeaders] = None
    cookies: Optional[SimpleCookie] = None
    ok: bool = False
    content_type: Optional[str] = None
    host: Optional[str] = None

    @classmethod
    def bad_response(cls) -> "Response":
        return cls(status_code=500, response_data=NetworkError)

    def __str__(self) -> str:
        return f"{self.status_code} from {self.url}. OK: {self.ok}"


@dataclass
class WrapperData:
    """ object: WrapperData """

    headers: dict
    data: Optional[dict] = None
    json: Optional[dict] = None
    cookies: Optional[dict] = None


__all__ = ("Response", "WrapperData")
