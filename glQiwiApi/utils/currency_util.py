from typing import Optional, Union

from glQiwiApi.types import _currencies
from glQiwiApi.types.amount import CurrencyModel


class Currency:
    __slots__ = ()

    @classmethod
    def get(cls, currency_code: Union[str, int]) -> Optional[CurrencyModel]:
        """
        Implements class-based getitem behaviour

        >>> Currency.get('840').symbol
        ... '$'
        >>> Currency.get('USD').symbol
        ... '$'
        :param currency_code: ISO 4217 string or CODE
        :return: Currency object
        """
        if isinstance(currency_code, int) or currency_code.isdigit():
            return _currencies.described.get(_currencies.codes_number[str(currency_code)])
        else:
            return _currencies.described.get(currency_code.upper())
