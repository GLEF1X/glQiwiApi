from __future__ import annotations

from typing import Dict, Any


def make_payload(**kwargs: Any) -> Dict[Any, Any]:
    return {
        key: value for key, value in kwargs.items()
        if key not in ['cls', 'self'] and value is not None
    }
