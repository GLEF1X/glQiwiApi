from __future__ import annotations

from datetime import datetime
from typing import Optional, cast

import pytz

from glQiwiApi.utils.compat import Final

DEFAULT_QIWI_TIMEZONE: Final[str] = "Europe/Moscow"


def datetime_to_utc(obj: datetime) -> str:
    iso_format_date = pytz.utc.localize(obj).replace(tzinfo=None).isoformat(" ")
    return iso_format_date.replace(" ", "T") + "Z"


def datetime_to_iso8601_with_moscow_timezone(obj: Optional[datetime]) -> str:
    """
    Converts a date to a standard format for API's

    :param obj: datetime object to parse to string
    :return: string - parsed date
    """
    if not isinstance(obj, datetime):
        return ""  # pragma: no cover
    return obj.astimezone(pytz.timezone(DEFAULT_QIWI_TIMEZONE)).isoformat(timespec='seconds')
