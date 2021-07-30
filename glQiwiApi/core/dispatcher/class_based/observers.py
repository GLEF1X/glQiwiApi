from __future__ import annotations

import abc
from typing import Any


class Observer(abc.ABC):
    @abc.abstractmethod
    async def process_event(self, event: Any) -> Any:
        raise NotImplementedError

    async def __call__(self, event: Any) -> Any:
        return await self.process_event(event)
