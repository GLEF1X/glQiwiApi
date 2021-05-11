from datetime import timedelta, datetime

from aiohttp import ClientTimeout

DEFAULT_TIMEOUT = ClientTimeout(total=5 * 60)

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
             '(KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'

uncached = (
    'https://api.qiwi.com/partner/bill',
    '/sinap/api/v2/terms/'
)

DEFAULT_BILL_TIME = datetime.now() + timedelta(days=2)
