from typing import Dict, ClassVar, List, Any


from glQiwiApi.base.api_method import APIMethod, ReturningType, Request
from glQiwiApi.qiwi.clients.wallet.types import Limit

ALL_LIMIT_TYPES = [
    "TURNOVER",
    "REFILL",
    "PAYMENTS_P2P",
    "PAYMENTS_PROVIDER_INTERNATIONALS",
    "PAYMENTS_PROVIDER_PAYOUT",
    "WITHDRAW_CASH",
]


class GetLimits(APIMethod[Dict[str, Limit]]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://edge.qiwi.com/qw-limits/v1/persons/{phone_number}/actual-limits"

    limit_types: List[str] = ALL_LIMIT_TYPES

    @classmethod
    def parse_response(cls, obj: Any) -> ReturningType:
        return {
            code: [Limit.parse_obj(limit) for limit in limits]
            for code, limits in obj["limits"].items()
        }

    def build_request(self, **url_format_kw: Any) -> Request:
        return Request(
            endpoint=self.url.format(**url_format_kw),
            params={f"types[{index}]": limit_type for index, limit_type in enumerate(self.limit_types)},
            http_method=self.http_method
        )
