from typing import Union, Optional, Any

from pydantic import BaseModel, Field

from glQiwiApi.utils import custom_load


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


class BillMixin:
    _w = None
    bill_id: Optional[str] = None

    def initialize(self, w: Any):
        self._w = w
        return self

    async def check(self) -> bool:
        return (await self._w.check_p2p_bill_status(bill_id=self.bill_id)) == 'PAID'


__all__ = [
    'Sum', 'OptionalSum', 'Commission', 'Type', 'BillMixin'
]
