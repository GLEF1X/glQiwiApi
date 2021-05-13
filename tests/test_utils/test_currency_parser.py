import pytest
from glQiwiApi.utils.currency_util import Currency, cur

pytestmark = pytest.mark.asyncio

_ = Currency()


async def test_currency_parser():
    from glQiwiApi.types.qiwi_types.currency_parsed import CurrencyModel
    condition = all(
        isinstance(_.get(key), CurrencyModel) for key in cur.described.keys()
    )
    assert condition
