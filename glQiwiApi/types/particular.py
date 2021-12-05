from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass
class WrappedRequestPayload:
    headers: Dict[Any, Any]
    json: Dict[Any, Any]
    data: Optional[Dict[Any, Any]] = None
    cookies: Optional[Dict[Any, Any]] = None


__all__ = ("WrappedRequestPayload",)
