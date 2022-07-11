from typing import Any, Dict, Optional

from pydantic import Field

from glQiwiApi.types.amount import Amount, Currency
from glQiwiApi.types.base import HashableBase


class AvailableBalance(HashableBase):
    alias: str
    currency: Currency


class Balance(HashableBase):
    """object: Balance"""

    alias: str
    title: str
    fs_alias: str = Field(alias='fsAlias')
    bank_alias: str = Field(alias='bankAlias')
    has_balance: bool = Field(alias='hasBalance')
    balance: Optional[Amount] = None
    currency: Currency
    account_type: Optional[Dict[str, Any]] = Field(None, alias='type')
    is_default_account: bool = Field(alias='defaultAccount')
