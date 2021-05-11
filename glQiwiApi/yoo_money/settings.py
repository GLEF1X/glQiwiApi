import functools
from dataclasses import dataclass
from typing import Any, Optional, Dict

from glQiwiApi.core.abstracts import AbstractRouter
from glQiwiApi.utils.basics import check_api_method


@dataclass
class YooMoneySettings:
    # Operations with token
    BUILD_URL_FOR_AUTH: str = '/oauth/authorize'
    GET_ACCESS_TOKEN: str = '/oauth/token'
    REVOKE_API_TOKEN: str = '/api/revoke'
    ACCOUNT_INFO: str = '/api/account-info'
    # Transactions
    TRANSACTIONS: str = '/api/operation-history'
    TRANSACTION_INFO: str = '/api/operation-details'
    # Payments
    PRE_PROCESS_PAYMENT: str = '/api/request-payment'
    PROCESS_PAYMENT: str = '/api/process-payment'
    ACCEPT_INCOMING_TRANSFER: str = '/api/incoming-transfer-accept'
    INCOMING_TRANSFER_REJECT: str = '/api/incoming-transfer-reject'

    def __init__(self):
        self.DEFAULT_YOOMONEY_HEADERS = {
            'Host': 'yoomoney.ru',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        self.ERROR_CODE_NUMBERS = {
            "400": "Ошибка, связанная с типом запроса к апи,"
                   "возможно вы передали недействительный API токен.",
            "401": "Указан несуществующий, просроченный, или отозванный токен.",
            "403": "Запрошена операция, на которую у токена нет прав.",
            "400_special_bad_proxy": "Ошибка, связанная с использованием прокси"
        }
        self.content_and_auth = {
            'content_json': True, 'auth': True
        }

    DEFAULT_YOOMONEY_HEADERS: Optional[Dict[str, str]] = None

    ERROR_CODE_NUMBERS: Optional[Dict[str, str]] = None

    content_and_auth: Optional[Dict[str, bool]] = None


class YooMoneyRouter(AbstractRouter):
    __head__ = 'https://yoomoney.ru'

    def setup_config(self) -> Any:
        return get_settings()

    @functools.lru_cache()
    def build_url(self, api_method: str, **kwargs: Any) -> str:
        check_api_method(api_method)
        tail_path: Optional[str] = getattr(self.config, api_method, None)
        pre_build_url = self.__head__ + tail_path
        return super()._format_url_kwargs(pre_build_url, **kwargs)


@functools.lru_cache()
def get_settings() -> YooMoneySettings:
    settings = YooMoneySettings()
    return settings


__all__ = ('YooMoneyRouter',)
