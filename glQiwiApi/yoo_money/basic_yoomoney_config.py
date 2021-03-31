# Ссылка для авторизации юмани
BASE_YOOMONEY_URL = 'https://yoomoney.ru'

DEFAULT_YOOMONEY_HEADERS = {
    'Host': 'yoomoney.ru',
    'Content-Type': 'application/x-www-form-urlencoded'
}

OPERATION_TRANSFER = {
    'datetime': 'operation_date',
    'type': 'operation_type'
}

content_and_auth = {'content_json': True, 'auth': True}

__all__ = (
    'DEFAULT_YOOMONEY_HEADERS',
    'BASE_YOOMONEY_URL', 'OPERATION_TRANSFER', 'content_and_auth'
)
