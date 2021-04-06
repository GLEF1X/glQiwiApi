from typing import Union

from pydantic import BaseModel, Field

from glQiwiApi.utils.basics import custom_load


class Sum(BaseModel):
    amount: Union[int, float, str]
    currency: str

    class Config:
        json_loads = custom_load


class OptionalSum(BaseModel):
    value: Union[int, float]
    currency: str


class Commission(BaseModel):
    provider_id: int = Field(alias="providerId")
    withdraw_sum: Sum = Field(alias="withdrawSum")
    enrollment_sum: Sum = Field(alias="enrollmentSum")
    qiwi_commission: Sum = Field("qwCommission")
    withdraw_to_enrollment_rate: int = Field(alias="withdrawToEnrollmentRate")

    class Config:
        json_loads = custom_load


class Type(BaseModel):
    id: str
    title: str


__all__ = [
    'Sum', 'OptionalSum', 'Commission', 'Type'
]
