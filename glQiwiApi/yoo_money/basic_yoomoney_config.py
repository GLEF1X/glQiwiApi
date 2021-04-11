# Ссылка для отправки запросов yoomoney
BASE_YOOMONEY_URL = 'https://yoomoney.ru'

DEFAULT_YOOMONEY_HEADERS = {
    'Host': 'yoomoney.ru',
    'Content-Type': 'application/x-www-form-urlencoded'
}

ERROR_CODE_NUMBERS = {
    "400": "Ошибка, связанная с типом запроса к апи,"
           "возможно вы передали недействительный API токен.",
    "401": "Указан несуществующий, просроченный, или отозванный токен.",
    "403": "Запрошена операция, на которую у токена нет прав.",
    "400_special_bad_proxy": "Ошибка, связанная с использованием прокси"
}

OPERATION_TRANSFER = {
    'datetime': 'operation_date',
    'type': 'operation_type'
}

content_and_auth = {'content_json': True, 'auth': True}

__all__ = (
    'DEFAULT_YOOMONEY_HEADERS', 'ERROR_CODE_NUMBERS',
    'BASE_YOOMONEY_URL', 'OPERATION_TRANSFER', 'content_and_auth'
)
