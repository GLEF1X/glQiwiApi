from pydantic import Field

from glQiwiApi.types.amount import Amount
from glQiwiApi.types.base import Base


class Commission(Base):
    provider_id: int = Field(alias='providerId')
    withdraw_sum: Amount = Field(alias='withdrawSum')
    enrollment_sum: Amount = Field(alias='enrollmentSum')
    qiwi_commission: Amount = Field(alias='qwCommission')
    withdraw_to_enrollment_rate: int = Field(alias='withdrawToEnrollmentRate')
