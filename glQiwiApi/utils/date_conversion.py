from datetime import datetime, timezone
from typing import Optional

DEFAULT_QIWI_TIMEZONE = 'Europe/Moscow'

try:
    import zoneinfo
except ImportError:
    import backports.zoneinfo as zoneinfo


def datetime_to_utc_in_iso_format(obj: datetime) -> str:
    return obj.astimezone(tz=timezone.utc).isoformat(timespec='milliseconds')


def datetime_to_iso8601_with_moscow_timezone(obj: Optional[datetime]) -> str:
    """
    Converts a date to a standard format for API's

    :param obj: datetime object to parse to string
    :return: string - parsed date
    """
    if not isinstance(obj, datetime):
        return ''  # pragma: no cover
    return obj.astimezone(zoneinfo.ZoneInfo(DEFAULT_QIWI_TIMEZONE)).isoformat(timespec='seconds')
