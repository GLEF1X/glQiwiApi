from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytz

DEFAULT_QIWI_TIMEZONE = "Europe/Moscow"


def datetime_to_utc(obj: datetime) -> str:
    iso_format_date = pytz.utc.localize(obj).replace(tzinfo=None).isoformat(" ")
    return iso_format_date.replace(" ", "T") + "Z"


def datetime_to_iso8601(obj: Optional[datetime]) -> str:
    """
    Converts a date to a standard format for API's

    :param obj: datetime object to parse to string
    :return: string - parsed date
    """
    if not isinstance(obj, datetime):
        return ""  # pragma: no cover
    naive_datetime = obj.replace(microsecond=0)
    return (
        pytz.timezone(DEFAULT_QIWI_TIMEZONE)
            .localize(naive_datetime)
            .isoformat()
    )
