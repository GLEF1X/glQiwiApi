from datetime import timedelta, datetime

from aiohttp import ClientTimeout

DEFAULT_TIMEOUT = ClientTimeout(total=5 * 60)

UNCACHED = ("https://api.qiwi.com/partner/bill", "/sinap/api/v2/terms/")


def get_default_bill_time() -> datetime:
    return datetime.now() + timedelta(days=2)


DEFAULT_QIWI_TIMEZONE = 'Europe/Moscow'

DEFAULT_BILL_STATUSES = "READY_FOR_PAY"
