from __future__ import annotations

import contextvars
import copy
import logging
from types import TracebackType
from typing import (
    Any,
    TypeVar,
    Optional,
    cast,
    Generic,
    ClassVar,
    Dict,
    Type,
    Union, TYPE_CHECKING,
)

from glQiwiApi.core.dispatcher.dispatcher import (
    Dispatcher,
    TxnRawHandler,
    TxnFilters,
    BillFilters,
    BillRawHandler,
    ErrorRawHandler,
)
from glQiwiApi.core.dispatcher.filters import BaseFilter

if TYPE_CHECKING:
    from glQiwiApi.core.request_service import RequestService

_T = TypeVar("_T", bound="AsyncContextMixin")


class AsyncContextMixin:
    """Object: ToolsMixin"""
    _request_service: RequestService

    async def __aenter__(self):
        await self._request_service.warmup()
        return self

    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_value: Optional[BaseException],
            traceback: Optional[TracebackType],
    ) -> None:
        pass
        await self.close()

    async def close(self) -> None:
        await self._request_service.shutdown()

    def _get(self, item: Any) -> Any:  # pragma: no cover
        try:
            return super().__getattribute__(item)
        except AttributeError:
            return None

    def __deepcopy__(self, memo: Any) -> AsyncContextMixin:  # pragma: no cover
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
        return cast(AsyncContextMixin, result)


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


class HandlerCollectionMixin:
    _dispatcher: Optional[Dispatcher]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__()
        cls._dispatcher = None

    @property
    def dispatcher(self) -> Dispatcher:
        if not self._dispatcher:
            self._dispatcher = Dispatcher()
        return self._dispatcher

    @dispatcher.setter
    def dispatcher(self, other: Dispatcher) -> None:
        if not isinstance(other, Dispatcher):
            raise TypeError(f"Expected `Dispatcher`, got wrong type {type(other)}")
        self._dispatcher = other

    @property
    def transaction_handler(self):  # type: ignore
        """
        Handler manager for default QIWI transactions,
        you can pass on lambda filter, if you want,
        but it must to return a boolean
        """
        return self.dispatcher.transaction_handler

    @property
    def error_handler(self):  # type: ignore
        return self.dispatcher.error_handler

    @property
    def bill_handler(self):  # type: ignore
        """
        Handler manager for P2P bills,
        you can pass on lambda filter, if you want
        But it must to return a boolean
        """
        return self.dispatcher.bill_handler

    def register_transaction_handler(
            self, event_handler: TxnRawHandler, *filters: TxnFilters
    ) -> None:
        return self.dispatcher.register_transaction_handler(event_handler, *filters)

    def register_bill_handler(
            self, event_handler: BillRawHandler, *filters: BillFilters
    ) -> None:
        return self.dispatcher.register_bill_handler(event_handler, *filters)

    def register_error_handler(
            self,
            event_handler: ErrorRawHandler,
            exception: Optional[Union[Type[Exception], Exception]] = None,
            *filters: BaseFilter[Exception],
    ) -> None:
        return self.dispatcher.register_error_handler(
            event_handler, exception, *filters
        )

    @property
    def logger(self) -> logging.Logger:
        return self.dispatcher.logger
