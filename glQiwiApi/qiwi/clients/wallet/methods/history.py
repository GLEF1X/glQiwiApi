from datetime import datetime
from typing import Optional, List, Final, Dict, Any, ClassVar


from pydantic import root_validator, conint, Field

from glQiwiApi.base.api_method import APIMethod, Request
from glQiwiApi.qiwi.clients.wallet.types import History, TransactionType, Source
from glQiwiApi.utils.dates_conversion import datetime_to_iso8601_with_moscow_timezone

MAX_HISTORY_LIMIT: Final[int] = 50


class GetHistory(APIMethod[History]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://edge.qiwi.com/payment-history/v2/persons/{phone_number}/payments"

    rows: conint(le=MAX_HISTORY_LIMIT, strict=True, gt=0) = MAX_HISTORY_LIMIT
    transaction_type: TransactionType = Field(TransactionType.ALL, alias="type")
    sources: Optional[List[Source]] = None
    start_date: Optional[datetime] = Field(None, alias="startDate")
    end_date: Optional[datetime] = Field(None, alias="endDate")

    class Config:
        use_enum_values = True

    @root_validator()
    def check_start_date_is_not_greater_than_end_date(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        start_date: Optional[datetime] = values.get("start_date")
        end_date: Optional[datetime] = values.get("end_date")

        both_are_not_transmitted = start_date is None and end_date is None

        if both_are_not_transmitted:
            return values

        only_start_date_transmitted = start_date is not None and end_date is None
        only_end_date_transmitted = start_date is None and end_date is not None

        if only_start_date_transmitted or only_end_date_transmitted:
            raise ValueError(
                "You must transmit both start_date and end_date parameters to get history rather than one"
            )

        if (end_date - start_date).total_seconds() <= 0:
            raise ValueError("end_date cannot be bigger than start_date")

        return values

    def build_request(self, **url_format_kw: Any) -> Request:
        data = self.dict(exclude={"sources"}, exclude_none=True, by_alias=True)

        if data.get("startDate") and data.get("endDate"):
            data["startDate"] = datetime_to_iso8601_with_moscow_timezone(data["startDate"])
            data["endDate"] = datetime_to_iso8601_with_moscow_timezone(data["endDate"])

        if self.sources is None:
            return Request(endpoint=self.url.format(**url_format_kw), params=data)

        for index, source in enumerate(self.sources, start=1):
            data.update({f"source[{index}]": source.value})

        return Request(endpoint=self.url.format(**url_format_kw), params=data)
