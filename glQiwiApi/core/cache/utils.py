from __future__ import annotations

import time
from typing import Any, Dict

from glQiwiApi.core.cache.constants import VALUE_PLACEHOLDER, ADD_TIME_PLACEHOLDER


def embed_cache_time(**kwargs: Any) -> Dict[Any, Any]:
    return {
        key: {
            VALUE_PLACEHOLDER: value,
            ADD_TIME_PLACEHOLDER: time.monotonic()
        }
        for key, value in kwargs.items()
    }
