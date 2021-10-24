from __future__ import annotations

from typing import TYPE_CHECKING, Hashable

from pydantic import BaseModel, Extra

if TYPE_CHECKING:
    from glQiwiApi.qiwi.client import QiwiWrapper


class Base(BaseModel):
    @property
    def client(self) -> "QiwiWrapper":
        """Returning an instance of :class:`QiwiWrapper`"""
        from glQiwiApi.qiwi.client import QiwiWrapper

        instance = QiwiWrapper.get_current()

        if instance is None:
            raise RuntimeError(
                "Can't get client instance from context. "
                "You can fix this by setting the current instance: "
                "`QiwiWrapper.set_current(...)`"
            )
        return instance


class HashableBase(Base):
    class Config:
        allow_mutation = False

    def __hash__(self) -> int:
        return hash((type(self),) + tuple(self.__dict__.values()))

    def __eq__(self, other: Hashable) -> bool:
        return self.__hash__() == other.__hash__()


class ExtraBase(Base):
    class Config:  # pragma: no cover
        extra = Extra.allow
