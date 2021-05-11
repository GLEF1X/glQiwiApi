from pydantic import BaseModel, validator

from glQiwiApi.types.qiwi_types.currency_parsed import CurrencyModel
from glQiwiApi.utils.currency_util import Currency


class Balance(BaseModel):
    """ object: Balance """
    alias: str
    currency: CurrencyModel

    @validator("currency", pre=True, check_fields=True)
    def humanize_pay_currency(cls, v):
        if not isinstance(v, int):
            return v
        return Currency.get(str(v))
