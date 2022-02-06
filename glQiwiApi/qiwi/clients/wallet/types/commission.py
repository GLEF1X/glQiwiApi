from pydantic import Field

from glQiwiApi.types.amount import AmountWithCurrency
from glQiwiApi.types.base import Base


class Commission(Base):
    provider_id: int = Field(alias="providerId")
    withdraw_sum: AmountWithCurrency = Field(alias="withdrawSum")
    enrollment_sum: AmountWithCurrency = Field(alias="enrollmentSum")
    qiwi_commission: AmountWithCurrency = Field(alias="qwCommission")
    withdraw_to_enrollment_rate: int = Field(alias="withdrawToEnrollmentRate")
