from datetime import datetime
from typing import ClassVar, Union, Optional, Iterable, Any

from pydantic import conint

from glQiwiApi.core.abc.api_method import APIMethod, Request
from glQiwiApi.utils.date_conversion import datetime_to_utc_in_iso_format
from glQiwiApi.utils.payload import filter_dictionary_none_values
from glQiwiApi.yoo_money.types.types import OperationHistory

MAX_HISTORY_LIMIT = 100


class OperationHistoryMethod(APIMethod[OperationHistory]):
    http_method: ClassVar[str] = "GET"
    url: ClassVar[str] = "https://yoomoney.ru/api/operation-history"

    operation_types: Optional[Iterable[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    start_record: Optional[int] = None
    records: conint(le=MAX_HISTORY_LIMIT, strict=True, gt=0) = 30
    label: Optional[Union[str, int]] = None
    in_detail: bool = False

    def build_request(self, **url_format_kw: Any) -> "Request":
        payload = {
            "records": self.records,
            "label": self.label,
            "start_record": self.start_record,
            "details": str(self.in_detail).lower(),
        }

        if self.operation_types is not None:
            payload["type"] = " ".join([op_type.lower() for op_type in self.operation_types])
        if self.start_date:
            payload["from"] = datetime_to_utc_in_iso_format(self.start_date)
        if self.end_date:
            payload["till"] = datetime_to_utc_in_iso_format(self.end_date)

        return Request(
            endpoint=self.url.format(**url_format_kw, **self._get_runtime_path_values()),
            http_method=self.http_method,
            data=filter_dictionary_none_values(payload),
        )
