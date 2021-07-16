from __future__ import annotations

from dataclasses import dataclass
from typing import Union, Any, Optional, Tuple, Dict

from pydantic import BaseModel, validator

DEFAULT_CACHE_TIME = 0


class Sum(BaseModel):
    """
    Сумма платежа

    """

    amount: Union[int, float, str]
    currency: Any

    @validator("currency", pre=True)
    def humanize_pay_currency(cls, v):  # type: ignore
        from glQiwiApi.utils.currency_util import Currency

        if not isinstance(v, int):
            try:
                v = int(v)
            except ValueError:
                return v
        return Currency.get(str(v))


class OptionalSum(BaseModel):
    """object: OptionalSum"""

    value: Union[int, float]
    currency: str


class Type(BaseModel):
    """
    Базовая модель типа данных

    """

    id: str
    title: str


@dataclass
class Attributes:
    """
    Аттрибуты кэшированного запроса

    """

    headers: Optional[Dict[Any, Any]] = None
    json: Optional[Dict[Any, Any]] = None
    params: Optional[Dict[Any, Any]] = None
    data: Optional[Dict[Any, Any]] = None

    @classmethod
    def format(cls, kwargs: Dict[Any, Any], args: Tuple[Any, ...]) -> Attributes:
        return cls(
            **{k: kwargs.get(k) for k in args if isinstance(kwargs.get(k), dict)}
        )


@dataclass
class Cached:
    """
    Объект кэшированного запроса

    """

    kwargs: Attributes
    response_data: Any
    method: Optional[Any]


__all__ = ["Sum", "OptionalSum", "Type", "Cached", "DEFAULT_CACHE_TIME", "Attributes"]
