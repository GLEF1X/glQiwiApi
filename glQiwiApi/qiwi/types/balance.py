from pydantic import validator

from glQiwiApi.base_types.amount import CurrencyModel
from glQiwiApi.base_types.base import HashableBase
from glQiwiApi.utils.currency_util import Currency


class Balance(HashableBase):
    """object: Balance"""

    alias: str
    currency: CurrencyModel

    @validator("currency", pre=True)
    def humanize_pay_currency(cls, v):  # type: ignore
        if not isinstance(v, int):
            return v
        return Currency.get(str(v))
