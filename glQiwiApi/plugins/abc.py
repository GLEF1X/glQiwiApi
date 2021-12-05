import abc
from typing import Any, Dict


class Pluggable(abc.ABC):
    """Something pluggable into library"""

    @abc.abstractmethod
    async def incline(self, ctx: Dict[Any, Any]) -> Any:
        ...

    @abc.abstractmethod
    async def shutdown(self) -> None:
        ...
