from typing import Optional, Union

from glQiwiApi.types.qiwi_types import currency_parsed as cur


class Currency:
    """
    Class with many currencies
    >>> usd = Currency.get('840')
    >>> usd
    ... cur.CurrencyModel(code='USD', decimal_digits=2, name='US Dollar', name_plural='US dollars', rounding=0, symbol='$', symbol_native='$')
    >>> usd.symbol
    ... '$'
    """

    @classmethod
    def get(cls, currency_code: Union[str, int]) -> Optional[
        cur.CurrencyModel
    ]:
        """
        Implements class-based getitem behaviour
        >>> Currency.get('840').symbol
        ... '$'
        >>> Currency.get('USD').symbol
        ... '$'
        :param currency_code: ISO 4217 string or CODE
        :return: Currency object
        """
        try:
            if isinstance(currency_code, int) or currency_code.isdigit():
                return cur.described.get(cur.codes_number[str(currency_code)])
            else:
                return cur.described.get(currency_code.upper())
        except (KeyError, AssertionError):
            raise ValueError(
                f"Currency code `{currency_code}` was not found"
            )
