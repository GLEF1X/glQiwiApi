from datetime import timedelta, datetime

DEFAULT_TIMEOUT = 20

UNCACHED = ("https://api.qiwi.com/partner/bill", "/sinap/api/v2/terms/")

DEFAULT_CACHE_TIME = 0

TIMEOUT_IF_EXCEPTION = 40


def get_default_bill_time() -> datetime:
    return datetime.now() + timedelta(days=2)


DEFAULT_QIWI_TIMEZONE = "Europe/Moscow"

DEFAULT_BILL_STATUSES = "READY_FOR_PAY"

DEFAULT_APPLICATION_KEY = "__aiohttp_web_application__"
