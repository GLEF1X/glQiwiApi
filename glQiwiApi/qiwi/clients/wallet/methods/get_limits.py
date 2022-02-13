from typing import Dict, ClassVar, List, Any, Sequence

from glQiwiApi.core.abc.api_method import ReturningType, Request
from glQiwiApi.core.session.holder import HTTPResponse
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import Limit

ALL_LIMIT_TYPES = [
    "TURNOVER",
    "REFILL",
    "PAYMENTS_P2P",
    "PAYMENTS_PROVIDER_INTERNATIONALS",
    "PAYMENTS_PROVIDER_PAYOUT",
    "WITHDRAW_CASH",
]


class GetLimits(QiwiAPIMethod[Dict[str, Limit]]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://edge.qiwi.com/qw-limits/v1/persons/{phone_number}/actual-limits"

    limit_types: Sequence[str] = ALL_LIMIT_TYPES

    @classmethod
    def parse_http_response(cls, response: HTTPResponse) -> Dict[str, Limit]:
        return {
            code: [Limit.parse_obj(limit) for limit in limits]
            for code, limits in response.json()["limits"].items()
        }

    def build_request(self, **url_format_kw: Any) -> Request:
        return Request(
            endpoint=self.url.format(**url_format_kw),
            params={
                f"types[{index}]": limit_type for index, limit_type in enumerate(self.limit_types)
            },
            http_method=self.http_method,
        )
