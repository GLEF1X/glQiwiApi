import inspect
from typing import Any, Dict, cast

from iso4217 import Currency as _Currency
from iso4217 import find_currency
from pydantic import root_validator

from glQiwiApi.types.base import Base, HashableBase


class Currency(HashableBase, _Currency):
    __root__: int

    @root_validator(skip_on_failure=True)
    def humanize(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        currency_numeric_code: int = cast(int, values.get('__root__'))
        # inspect.getfullargspec(_Currency.__init__) will contain `self`,
        # so we cut it off and get original currency cls's constructor input names
        args = inspect.getfullargspec(_Currency.__init__).args[1:]
        currency = find_currency(numeric_code=currency_numeric_code)
        return {k: getattr(currency, k, None) for k in args}


class Amount(Base):
    value: float
    currency: Currency


class HashableAmount(Amount, HashableBase):
    pass
