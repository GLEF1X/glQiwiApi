from datetime import timedelta, datetime

from aiohttp import ClientTimeout

DEFAULT_TIMEOUT = ClientTimeout(total=5 * 60)

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    "(KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
)

UNCACHED = ("https://api.qiwi.com/partner/bill", "/sinap/api/v2/terms/")


def get_default_bill_time() -> datetime:
    return datetime.now() + timedelta(days=2)


DEFAULT_QIWI_TIMEZONE = 'Europe/Moscow'
