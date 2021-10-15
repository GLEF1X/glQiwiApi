from datetime import timedelta, datetime

DEFAULT_TIMEOUT = 20

NO_CACHING = 0

TIMEOUT_IF_EXCEPTION = 40


def get_default_bill_time() -> datetime:
    return datetime.now() + timedelta(days=2)


DEFAULT_BILL_STATUSES = "READY_FOR_PAY"

DEFAULT_APPLICATION_KEY = "__aiohttp_web_application__"
