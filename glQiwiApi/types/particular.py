from dataclasses import dataclass
from http.cookies import SimpleCookie
from typing import Optional, Union, Dict

from aiohttp.typedefs import RawHeaders

from glQiwiApi.utils.exceptions import ProxyError

response_type = Union[dict, str, bytes, bytearray, Exception, list]


@dataclass
class Response:
    """ object: Response """
    status_code: int
    response_data: Optional[response_type] = None
    url: Optional[str] = None
    raw_headers: Optional[RawHeaders] = None
    cookies: Optional[SimpleCookie] = None
    ok: bool = False
    content_type: Optional[str] = None
    host: Optional[str] = None

    @classmethod
    def bad_response(cls) -> 'Response':
        return cls(
            status_code=500,
            response_data=ProxyError
        )

    def __str__(self) -> str:
        return f"{self.status_code} from {self.url}. OK: {self.ok}"


@dataclass
class WrapperData:
    """ object: WrapperData """
    headers: Dict[str, Union[str, int]]
    data: Dict[str, Union[str, Dict[str, str]]] = None
    json: Dict[str, Union[str, Dict[str, str]]] = None
    cookies: Optional[Dict[str, Union[str, int]]] = None


__all__ = (
    'Response', 'WrapperData'
)
