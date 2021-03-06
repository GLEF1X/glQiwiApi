from pydantic import Field

from glQiwiApi.types.base import ExtraBase
from glQiwiApi.types.basics import Sum


class Commission(ExtraBase):
    provider_id: int = Field(alias="providerId")
    withdraw_sum: Sum = Field(alias="withdrawSum")
    enrollment_sum: Sum = Field(alias="enrollmentSum")
    qiwi_commission: Sum = Field(alias="qwCommission")
    withdraw_to_enrollment_rate: int = Field(alias="withdrawToEnrollmentRate")
