import pytest
from iso4217 import CurrencyNotFoundError

from glQiwiApi.types.amount import Currency


def test_currency_from_code() -> None:
    hryvna_currency = Currency.parse_obj(980)
    assert hryvna_currency.dict(exclude_none=True) == {
        'alphabetical_code': 'UAH',
        'currency_name': 'Hryvnia',
        'entity': 'UKRAINE',
        'decimal_places': 2,
        'numeric_code': 980,
    }


def test_fail_if_currency_not_found() -> None:
    with pytest.raises(CurrencyNotFoundError):
        defunct_currency = Currency.parse_obj(656)
