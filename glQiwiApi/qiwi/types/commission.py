from pydantic import Field

from glQiwiApi.base_types.amount import AmountWithCurrency
from glQiwiApi.qiwi.types.base import QiwiWalletResultBaseWithClient


class Commission(QiwiWalletResultBaseWithClient):
    provider_id: int = Field(alias="providerId")
    withdraw_sum: AmountWithCurrency = Field(alias="withdrawSum")
    enrollment_sum: AmountWithCurrency = Field(alias="enrollmentSum")
    qiwi_commission: AmountWithCurrency = Field(alias="qwCommission")
    withdraw_to_enrollment_rate: int = Field(alias="withdrawToEnrollmentRate")
