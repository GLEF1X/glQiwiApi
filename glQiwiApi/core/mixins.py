from __future__ import annotations

from typing import Any, Dict, Optional, Type, Union, cast

from glQiwiApi.core.dispatcher.filters import BaseFilter
from glQiwiApi.core.dispatcher.implementation import (
    BillFilters,
    BillRawHandler,
    Dispatcher,
    ErrorRawHandler,
    TxnFilters,
    TxnRawHandler,
)


class DataMixin:
    @property
    def ctx(self) -> Dict[Any, Any]:  # pragma: no cover
        data = getattr(self, "_data", None)
        if data is None:
            data = {}
            setattr(self, "_data", data)
        return cast(Dict[Any, Any], data)

    def __getitem__(self, item: Any) -> Any:
        return self.ctx[item]  # pragma: no cover

    def __setitem__(self, key: Any, value: Any) -> None:
        self.ctx[key] = value  # pragma: no cover

    def __delitem__(self, key: Any) -> None:
        del self.ctx[key]  # pragma: no cover

    def __contains__(self, key: Any) -> bool:
        return key in self.ctx  # pragma: no cover

    def get(self, key, default=None):  # type: ignore
        return self.ctx.get(key, default)  # pragma: no cover


class DispatcherShortcutsMixin:
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
        return self.dispatcher.transaction_handler

    @property
    def error_handler(self):  # type: ignore
        return self.dispatcher.error_handler

    @property
    def bill_handler(self):  # type: ignore
        return self.dispatcher.bill_handler

    def register_transaction_handler(
        self, event_handler: TxnRawHandler, *filters: TxnFilters
    ) -> None:
        return self.dispatcher.register_transaction_handler(event_handler, *filters)

    def register_bill_handler(self, event_handler: BillRawHandler, *filters: BillFilters) -> None:
        return self.dispatcher.register_bill_handler(event_handler, *filters)

    def register_error_handler(
        self,
        event_handler: ErrorRawHandler,
        exception: Optional[Union[Type[Exception], Exception]] = None,
        *filters: BaseFilter[Exception],
    ) -> None:
        return self.dispatcher.register_error_handler(event_handler, exception, *filters)
