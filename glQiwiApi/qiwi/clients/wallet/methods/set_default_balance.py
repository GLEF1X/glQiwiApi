from typing import Any, ClassVar, Dict

from pydantic import Field

from glQiwiApi.qiwi.base import QiwiAPIMethod


class SetDefaultBalance(QiwiAPIMethod[Dict[Any, Any]]):
    http_method: ClassVar[str] = 'PATCH'
    url: ClassVar[
        str
    ] = 'https://edge.qiwi.com/funding-sources/v2/persons/{phone_number}/accounts/{account_alias}'

    account_alias: str = Field(..., path_runtime_value=True)
