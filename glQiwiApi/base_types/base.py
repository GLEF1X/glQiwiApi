from __future__ import annotations

from typing import TYPE_CHECKING, Hashable, Any, TypeVar, Type, Generic, Dict, cast

from pydantic import BaseModel, BaseConfig, PrivateAttr

from glQiwiApi.utils.compat import json

if TYPE_CHECKING:
    from glQiwiApi.core.abc.wrapper import Wrapper  # noqa

_Client = TypeVar("_Client", bound="Wrapper")
T = TypeVar("T", bound="BaseWithClient[Any]")


class Base(BaseModel):
    _client_ctx: Dict[str, Any] = PrivateAttr(default_factory=dict)

    class Config(BaseConfig):
        json_dumps = json.dumps  # type: ignore
        json_loads = json.loads
        orm_mode = True


class HashableBase(Base):
    class Config(BaseConfig):
        allow_mutation = False

    def __hash__(self) -> int:
        return hash((type(self),) + tuple(self.__dict__.values()))

    def __eq__(self, other: Hashable) -> bool:
        return self.__hash__() == other.__hash__()


class BaseWithClient(Base, Generic[_Client]):
    @classmethod
    def from_obj(cls: Type[T], c: _Client, obj: Any) -> T:
        result = super().parse_obj(obj)
        result._client_ctx["client"] = c  # hack with faux immutability(described in pydantic docs)
        return result

    @property
    def client(self) -> _Client:
        return cast(_Client, self._client_ctx["client"])


class HashableBaseWithClient(HashableBase, BaseWithClient[_Client], Generic[_Client]):
    pass
