import time
from dataclasses import dataclass
from typing import Union, Any, Optional

from pydantic import BaseModel, Field, validator, Extra
from glQiwiApi.utils.basics import custom_load

DEFAULT_CACHE_TIME = 0


class Sum(BaseModel):
    """
    Сумма платежа

    """
    amount: Union[int, float, str]
    currency: Any

    class Config:
        """ Pydantic config """
        json_loads = custom_load
        extra = Extra.allow

        def __str__(self) -> str:
            return '<Config class of pydantic>'

        def __repr__(self) -> str:
            return self.__str__()

    @validator("currency", pre=True, check_fields=True)
    def humanize_pay_currency(cls, v):
        from glQiwiApi.utils.currency_util import Currency
        if not isinstance(v, int):
            return v
        return Currency.get(str(v))


class OptionalSum(BaseModel):
    """ object: OptionalSum """
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
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return '<Config class of pydantic>'

        def __repr__(self) -> str:
            return self.__str__()


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
class Cached:
    """
    Объект кэшированного запроса

    """
    kwargs: Attributes
    response_data: Any
    key: Optional[str]
    cache_to: Optional[Any]
    method: Optional[Any]
    cached_in: float = time.monotonic()
    status_code: Union[str, int, None] = None


__all__ = [
    'Sum',
    'OptionalSum',
    'Commission',
    'Type',
    'Cached',
    'DEFAULT_CACHE_TIME',
    'Attributes'
]
