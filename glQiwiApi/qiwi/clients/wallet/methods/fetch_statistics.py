from datetime import datetime, timedelta
from typing import ClassVar, List, Optional, Dict, Any

from pydantic import root_validator, Field

from glQiwiApi.core.abc.api_method import Request
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.wallet.types import Statistic, TransactionType
from glQiwiApi.utils.date_conversion import datetime_to_iso8601_with_moscow_timezone


class FetchStatistics(QiwiAPIMethod[Statistic]):
    url: ClassVar[
        str
    ] = "https://edge.qiwi.com/payment-history/v2/persons/{phone_number}/payments/total"
    http_method: ClassVar[str] = "GET"

    start_date: datetime = Field(default_factory=datetime.now)
    end_date: datetime = Field(default_factory=lambda: datetime.now() - timedelta(days=90))
    operation: TransactionType = TransactionType.ALL
    sources: Optional[List[str]] = None

    @root_validator()
    def check_start_date_and_end_date_difference_not_greater_than_90_days(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        start_date: Optional[datetime] = values.get("start_date")
        end_date: Optional[datetime] = values.get("end_date")

        if start_date is None or end_date is None:  # denotes that type of arguments is invalid
            return values

        if (end_date - start_date).days > 90 or (start_date - end_date).days > 90:
            raise ValueError("The maximum period for downloading statistics is 90 calendar days.")

        return values

    def build_request(self, **url_format_kw: Any) -> Request:
        params = {
            "startDate": datetime_to_iso8601_with_moscow_timezone(self.start_date),
            "endDate": datetime_to_iso8601_with_moscow_timezone(self.end_date),
            "operation": self.operation.value,
        }
        if self.sources:
            params.update({"sources": " ".join(self.sources)})
        return Request(
            endpoint=self.url.format(**url_format_kw), params=params, http_method=self.http_method
        )
