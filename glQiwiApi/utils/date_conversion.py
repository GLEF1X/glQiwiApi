import sys
from datetime import datetime, timezone
from typing import Optional

DEFAULT_QIWI_TIMEZONE = 'Europe/Moscow'

if sys.version_info < (3, 9, 0):
    try:
        import pytz
    except ImportError:
        raise RuntimeError(
            'glQiwiApi requires `pytz` package for python < 3.9'
            'as an alternative to a new builtin `zoneinfo`. '
            'Please install pytz using pip install pytz.'
        )

    def to_moscow(obj: datetime) -> datetime:
        return obj.astimezone(pytz.timezone(DEFAULT_QIWI_TIMEZONE))

else:
    import zoneinfo

    def to_moscow(obj: datetime) -> datetime:
        return obj.astimezone(zoneinfo.ZoneInfo(DEFAULT_QIWI_TIMEZONE))


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
    return to_moscow(obj).isoformat(timespec='seconds')
