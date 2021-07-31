from __future__ import annotations

import inspect
from abc import ABCMeta
from typing import Optional, Union, Any, Dict, TypeVar, Type

from glQiwiApi import async_as_sync, QiwiWrapper
from glQiwiApi.types.basics import DEFAULT_CACHE_TIME

_T = TypeVar("_T")


class SyncAdapterMeta(ABCMeta):

    def __new__(mcs: Type[_T], name: str, bases: tuple, attrs: Dict[Any, Any]) -> _T:
        for attr, value in bases[0].__dict__.items():
            if inspect.iscoroutinefunction(value):
                attrs[attr] = async_as_sync().__call__(value)

        return super().__new__(mcs, name, bases, attrs)  # type: ignore


class SyncAdaptedQiwi(QiwiWrapper, metaclass=SyncAdapterMeta):

    def __init__(
            self,
            api_access_token: Optional[str] = None,
            phone_number: Optional[str] = None,
            secret_p2p: Optional[str] = None,
            without_context: bool = True,
            cache_time: Union[float, int] = DEFAULT_CACHE_TIME,  # 0 by default
            validate_params: bool = False,
            proxy: Any = None,
    ) -> None:
        super(SyncAdaptedQiwi, self).__init__(api_access_token, phone_number=phone_number,
                                              secret_p2p=secret_p2p, without_context=without_context,
                                              cache_time=cache_time, validate_params=validate_params,
                                              proxy=proxy)
