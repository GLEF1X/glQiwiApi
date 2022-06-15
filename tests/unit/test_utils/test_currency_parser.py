from glQiwiApi.types._currencies import described
from glQiwiApi.types.amount import CurrencyModel
from glQiwiApi.utils.currency_util import Currency


def test_parse_described_currencies():
    condition = all(isinstance(Currency().get(key), CurrencyModel) for key in described.keys())
    assert condition


def test_parse_non_existent_currency():
    assert Currency().get(currency_code='dsfgsgdsfg') is None
