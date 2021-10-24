from __future__ import annotations

import functools
from typing import Any

from glQiwiApi.core.abc.router import AbstractRouter

__all__ = ("YooMoneyRouter", "YooMoneyMethods")


class YooMoneyRouter(AbstractRouter):
    __head__ = "https://yoomoney.ru"

    def setup_routes(self) -> Any:
        return YooMoneyMethods()

    def setup_config(self) -> YooMoneyConfig:
        return YooMoneyConfig()

    @functools.lru_cache()
    def build_url(self, tail: str, **kwargs: Any) -> str:
        pre_build_url = self.__head__ + tail
        return super()._format_url_kwargs(pre_build_url, **kwargs)


class YooMoneyConfig:
    def __init__(self) -> None:
        self.DEFAULT_YOOMONEY_HEADERS = {
            "Host": "yoomoney.ru",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        self.ERROR_CODE_MESSAGES = {
            400: "An error related to the type of request to the api,"
                 "you may have passed an invalid API token",
            401: "A non-existent, expired, or revoked token is specified",
            403: "An operation has been requested for which the token has no rights",
            0: "Proxy error or unexpected server errors",
        }
        self.content_and_auth = {"content_json": True, "auth": True}


class YooMoneyMethods:
    # Operations with token
    BUILD_URL_FOR_AUTH: str = "/oauth/authorize"
    GET_ACCESS_TOKEN: str = "/oauth/token"
    REVOKE_API_TOKEN: str = "/api/revoke"
    ACCOUNT_INFO: str = "/api/account-info"
    # Transactions
    TRANSACTIONS: str = "/api/operation-history"
    TRANSACTION_INFO: str = "/api/operation-details"
    # Payments
    PRE_PROCESS_PAYMENT: str = "/api/request-payment"
    PROCESS_PAYMENT: str = "/api/process-payment"
    ACCEPT_INCOMING_TRANSFER: str = "/api/incoming-transfer-accept"
    INCOMING_TRANSFER_REJECT: str = "/api/incoming-transfer-reject"

    # Forms
    QUICK_PAY_FORM: str = "/quickpay/confirm.xml?"
