from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from glQiwiApi.qiwi.client import QiwiWrapper


class Base(BaseModel):
    @property
    def client(self) -> QiwiWrapper:
        """ Returning an instance of :class:`QiwiWrapper` """
        from glQiwiApi.qiwi.client import QiwiWrapper

        instance = QiwiWrapper.get_current()

        if instance is None:
            raise RuntimeError(
                "Can't get client instance from context. "
                "You can fix it with setting current instance: "
                "'QiwiWrapper.set_current(wrapper_instance)'"
            )
        return instance
