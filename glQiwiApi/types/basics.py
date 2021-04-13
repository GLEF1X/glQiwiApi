import time
from dataclasses import dataclass
from typing import Union, Any, Optional

from pydantic import BaseModel, Field

from glQiwiApi.utils.basics import custom_load

DEFAULT_CACHE_TIME = 0


class Sum(BaseModel):
    """
    Сумма платежа

    """
    amount: Union[int, float, str]
    currency: str

    class Config:
        json_loads = custom_load


class OptionalSum(BaseModel):
    value: Union[int, float]
    currency: str


class Commission(BaseModel):
    """
    Комиссия за платеж

    """
    provider_id: int = Field(alias="providerId")
    withdraw_sum: Sum = Field(alias="withdrawSum")
    enrollment_sum: Sum = Field(alias="enrollmentSum")
    qiwi_commission: Sum = Field("qwCommission")
    withdraw_to_enrollment_rate: int = Field(alias="withdrawToEnrollmentRate")

    class Config:
        json_loads = custom_load


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
    headers: Optional[dict] = None
    json: Optional[dict] = None
    params: Optional[dict] = None
    data: Optional[dict] = None

    @classmethod
    def format(cls, kwargs: dict, args: tuple):
        return cls(
            **{k: kwargs.get(k) for k in args if
               isinstance(kwargs.get(k), dict)}
        )


@dataclass
class CachedResponse:
    """
    Объект кэшированного запроса

    """
    kwargs: Attributes
    response_data: Any
    status_code: Union[str, int]
    url: str
    method: str
    cached_in: float = time.monotonic()


__all__ = [
    'Sum',
    'OptionalSum',
    'Commission',
    'Type',
    'CachedResponse',
    'DEFAULT_CACHE_TIME',
    'Attributes'
]
