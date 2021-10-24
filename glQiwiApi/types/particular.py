from dataclasses import dataclass
from typing import Optional, Any, Dict

from aiohttp.typedefs import RawHeaders

from glQiwiApi.utils.exceptions import NetworkError


@dataclass
class Response:
    """object: Response"""

    status_code: int
    response_data: Any
    url: Optional[str] = None
    raw_headers: Optional[RawHeaders] = None
    cookies: Optional[Any] = None
    ok: bool = False
    content_type: Optional[str] = None
    host: Optional[str] = None

    @classmethod
    def bad_response(cls) -> "Response":
        return cls(status_code=500, response_data=NetworkError)

    def __str__(self) -> str:
        return f"{self.status_code} from {self.url}. OK: {self.ok}"


@dataclass
class WrappedRequestPayload:
    headers: Dict[Any, Any]
    json: Dict[Any, Any]
    data: Optional[Dict[Any, Any]] = None
    cookies: Optional[Dict[Any, Any]] = None


__all__ = ("Response", "WrappedRequestPayload")
