from __future__ import annotations

import contextvars
import copy
from typing import Any, TYPE_CHECKING, TypeVar, Optional, cast, Generic, ClassVar, Dict

if TYPE_CHECKING:
    from glQiwiApi.core.aiohttp_custom_api import RequestManager  # pragma: no cover


class ToolsMixin(object):
    """Object: ToolsMixin"""

    _requests: RequestManager

    async def __aenter__(self) -> ToolsMixin:
        await self._requests.create_session()
        return self

    async def close(self) -> None:
        await self._requests.close()

    async def __aexit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        await self.close()

    def _get(self, item: Any) -> Any:  # pragma: no cover
        try:
            return super().__getattribute__(item)
        except AttributeError:
            return None

    def __deepcopy__(self, memo: Any) -> ToolsMixin:  # pragma: no cover
        cls = self.__class__
        kw = {"__copy_signal__": True}
        result = cls.__new__(cls, **kw)  # type: ignore  # pragma: no cover
        memo[id(self)] = result
        dct = {
            slot: self._get(slot)
            for slot in self.__slots__
            if self._get(slot) is not None
        }
        for k, value in dct.items():
            if k == "_requests":
                value._session = None
            elif k == "dispatcher":
                value._loop = None
            setattr(result, k, copy.deepcopy(value, memo))  # NOQA
        return cast(ToolsMixin, result)


class DataMixin:

    @property
    def data(self) -> Dict[Any, Any]:  # pragma: no cover
        data = getattr(self, "_data", None)
        if data is None:
            data = {}
            setattr(self, "_data", data)
        return cast(Dict[Any, Any], data)

    def __getitem__(self, item: Any) -> Any:
        return self.data[item]  # pragma: no cover

    def __setitem__(self, key: Any, value: Any) -> None:
        self.data[key] = value  # pragma: no cover

    def __delitem__(self, key: Any) -> None:
        del self.data[key]  # pragma: no cover

    def __contains__(self, key: Any) -> bool:
        return key in self.data  # pragma: no cover

    def get(self, key, default=None):  # type: ignore
        return self.data.get(key, default)  # pragma: no cover


ContextInstance = TypeVar("ContextInstance")


class ContextInstanceMixin(Generic[ContextInstance]):
    __context_instance: ClassVar[contextvars.ContextVar[ContextInstance]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__()
        cls.__context_instance = contextvars.ContextVar(f"instance_{cls.__name__}")

    @classmethod  # noqa: F811
    def get_current(  # noqa: F811
            cls, no_error: bool = True
    ) -> Optional[ContextInstance]:  # pragma: no cover  # noqa: F811
        """Get current instance from context"""
        # on mypy 0.770 I catch that contextvars.ContextVar always contextvars.ContextVar[Any]
        cls.__context_instance = cast(
            contextvars.ContextVar[ContextInstance], cls.__context_instance
        )

        try:
            current: Optional[ContextInstance] = cls.__context_instance.get()
        except LookupError:
            if no_error:
                current = None
            else:
                raise

        return current

    @classmethod
    def set_current(cls, value: ContextInstance) -> contextvars.Token[ContextInstance]:
        if not isinstance(value, cls):
            raise TypeError(  # pragma: no cover
                f"Value should be instance of {cls.__name__!r} not {type(value).__name__!r}"
            )
        return cls.__context_instance.set(value)

    @classmethod
    def reset_current(cls, token: contextvars.Token[ContextInstance]) -> None:
        cls.__context_instance.reset(token)
