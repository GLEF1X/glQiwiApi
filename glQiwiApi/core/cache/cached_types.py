from __future__ import annotations

import http
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Union


class Payload:
    def __init__(
        self,
        headers: Optional[Dict[Any, Any]] = None,
        json: Optional[Dict[Any, Any]] = None,
        params: Optional[Dict[Any, Any]] = None,
        data: Optional[Dict[Any, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self.headers = headers
        self.json = json
        self.params = params
        self.data = data

    @classmethod
    def new(cls, kwargs: Dict[Any, Any], args: Tuple[Any, ...]) -> Payload:
        return cls(**{k: kwargs.get(k) for k in args if isinstance(kwargs.get(k), dict)})


@dataclass(frozen=True)
class CachedAPIRequest:
    payload: Payload
    response: Any
    method: Union[str, http.HTTPStatus]
