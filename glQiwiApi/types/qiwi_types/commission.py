from pydantic import Field

from glQiwiApi.types.base import ExtraBase
from glQiwiApi.types.amount import CurrencyAmount


class Commission(ExtraBase):
    provider_id: int = Field(alias="providerId")
    withdraw_sum: CurrencyAmount = Field(alias="withdrawSum")
    enrollment_sum: CurrencyAmount = Field(alias="enrollmentSum")
    qiwi_commission: CurrencyAmount = Field(alias="qwCommission")
    withdraw_to_enrollment_rate: int = Field(alias="withdrawToEnrollmentRate")
