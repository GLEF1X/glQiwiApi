from pydantic import validator

from glQiwiApi.types.base import Base
from glQiwiApi.types.amount import CurrencyModel
from glQiwiApi.utils.currency_util import Currency


class Balance(Base):
    """object: Balance"""

    alias: str
    currency: CurrencyModel

    @validator("currency", pre=True)
    def humanize_pay_currency(cls, v):  # type: ignore
        if not isinstance(v, int):
            return v
        return Currency.get(str(v))
