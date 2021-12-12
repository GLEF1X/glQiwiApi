import abc
from typing import Any, Dict


class Pluggable(abc.ABC):
    """Something pluggable into library"""

    @abc.abstractmethod
    async def install(self, ctx: Dict[Any, Any]) -> None:
        ...

    @abc.abstractmethod
    async def shutdown(self) -> None:
        ...
