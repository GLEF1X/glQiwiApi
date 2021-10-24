from __future__ import annotations

import time
from copy import deepcopy
from typing import Any, Dict

from glQiwiApi.core.abc.router import AbstractRouter
from glQiwiApi.types import WrappedRequestPayload
from glQiwiApi.utils.mypy_hacks import lru_cache

__all__ = ("get_config", "QiwiRouter", "QiwiKassaRouter", "QiwiApiMethods")


@lru_cache()
def get_config() -> QiwiConfig:
    return QiwiConfig()


class QiwiRouter(AbstractRouter):
    """The class that instructs to build the right paths except for QIWI P2P API"""

    __head__ = "https://edge.qiwi.com"

    def setup_routes(self) -> Any:
        return QiwiApiMethods()

    @lru_cache(typed=True)
    def build_url(self, api_method: str, **kwargs: Any) -> str:
        pre_build_url = self.__head__ + api_method
        return super()._format_url_kwargs(pre_build_url, **kwargs)

    def setup_config(self) -> QiwiConfig:
        return get_config()

    def generate_default_headers(self) -> Dict[Any, Any]:
        return deepcopy(self.config.DEFAULT_QIWI_HEADERS)


class QiwiKassaRouter(QiwiRouter):
    """QIWI P2P router"""

    __head__ = "https://api.qiwi.com/partner/bill/v1/bills"


class QiwiApiMethods:
    # Qiwi Wallet
    TO_CARD: str = "/sinap/api/v2/terms/{privat_card_id}"
    GET_BALANCE: str = "/funding-sources/v2/persons/{phone_number}/accounts"
    TRANSACTIONS: str = "/payment-history/v2/persons/{stripped_number}/payments"
    TO_WALLET: str = "/sinap/api/v2/terms/99/payments"
    TRANSACTION_INFO: str = "/payment-history/v1/transactions/{transaction_id}"
    CHECK_RESTRICTION: str = (
        "/person-profile/v1/persons/{phone_number}/status/restrictions"
    )
    GET_IDENTIFICATION: str = "/identification/v1/persons/{phone_number}/identification"
    GET_LIMITS: str = "/qw-limits/v1/persons/{stripped_number}/actual-limits"
    GET_LIST_OF_CARDS: str = "/cards/v1/cards"
    AUTHENTICATE: str = "/identification/v1/persons/{stripped_number}/identification"
    GET_BILLS: str = "/checkout-api/api/bill/search"
    GET_RECEIPT: str = "/payment-history/v1/transactions/{transaction_id}/cheque/file"
    COMMISSION: str = "/sinap/providers/{special_code}/onlineCommission"
    ACCOUNT_INFO: str = "/person-profile/v1/profile/current"
    FETCH_STATISTICS: str = (
        "/payment-history/v2/persons/{stripped_number}/payments/total"
    )
    LIST_OF_BALANCES: str = "/funding-sources/v2/persons/{stripped_number}/accounts"
    CREATE_NEW_BALANCE: str = "/funding-sources/v2/persons/{stripped_number}/accounts"
    AVAILABLE_BALANCES: str = (
        "/funding-sources/v2/persons/{stripped_number}/accounts/offer"
    )
    SET_DEFAULT_BALANCE: str = (
        "/funding-sources/v2/persons/{stripped_number}/accounts/{currency_alias}"
    )
    BUY_QIWI_MASTER: str = "/sinap/api/v2/terms/28004/payments"
    CONFIRM_QIWI_MASTER: str = (
        "/cards/v2/persons/{stripped_number}/orders/{order_id}/submit"
    )
    BUY_QIWI_CARD = "/sinap/test_core/v2/terms/32064/payments"
    CARDS_QIWI_MASTER: str = "/cards/v1/cards/?vas-alias=qvc-master"
    PRE_QIWI_REQUEST: str = "/cards/v2/persons/{number}/orders"
    GET_CROSS_RATES: str = "/sinap/crossRates"
    SPECIAL_PAYMENT: str = "/sinap/api/v2/terms/1717/payments"

    # Qiwi P2P
    CREATE_P2P_BILL: str = "/{bill_id}"
    CHECK_P2P_BILL_STATUS: str = "/{bill_id}"
    REJECT_P2P_BILL: str = "/{bill_id}/reject"
    REFUND_BILL: str = "/{bill_id}/refunds/{refund_id}"
    CREATE_P2P_KEYS: str = "/widgets-api/api/p2p/protected/keys/create"

    # Webhooks
    REG_WEBHOOK: str = "/payment-notifier/v1/hooks"
    GET_CURRENT_WEBHOOK: str = "/payment-notifier/v1/hooks/active"
    SEND_TEST_NOTIFICATION: str = "/payment-notifier/v1/hooks/test"
    GET_WEBHOOK_SECRET: str = "/payment-notifier/v1/hooks/{hook_id}/key"
    DELETE_CURRENT_WEBHOOK: str = "/payment-notifier/v1/hooks/{hook_id}"
    CHANGE_WEBHOOK_SECRET: str = "/payment-notifier/v1/hooks/{hook_id}/newkey"


class QiwiConfig:
    def __init__(self) -> None:
        self.DEFAULT_QIWI_HEADERS = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer {token}",
            "Host": "edge.test_qiwi.com",
        }
        self.P2P_QIWI_HEADERS = {
            "Authorization": "Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.ERROR_CODE_MESSAGES = {
            400: "Insufficient funds for the operation",
            401: "Invalid token or API token was expired",
            403: "No permission for this request(API token has insufficient permissions)",
            404: "Object was not found or there are no objects with the specified characteristics",
            423: "Too many requests, the service is temporarily unavailable",
            422: "The domain / subnet / host is incorrectly specified"
                 "webhook (in the new_url parameter for the webhook URL),"
                 "the hook type or transaction type is incorrectly specified,"
                 "an attempt to create a hook if there is one already created",
            405: "Error related to the type of API request, contact the developer or open an issue",
            500: "Internal service error",
            0: "An error related to using a proxy or library problems",
        }
        self.QIWI_MASTER = {
            "id": str(int(time.time() * 1000)),
            "sum": {"amount": 2999, "currency": "643"},
            "paymentMethod": {"type": "Account", "accountId": "643"},
            "comment": "test",
            "fields": {"account": "", "vas_alias": "qvc-master"},
        }
        self.QIWI_TO_CARD: WrappedRequestPayload = WrappedRequestPayload(
            json={
                "id": str(int(time.time() * 1000)),
                "sum": {"amount": "", "currency": "643"},
                "paymentMethod": {"type": "Account", "accountId": "643"},
                "fields": {"account": ""},
            },
            headers=self.DEFAULT_QIWI_HEADERS,
        )

        self.P2P_DATA: WrappedRequestPayload = WrappedRequestPayload(
            json={
                "amount": {"currency": "RUB", "value": "{amount}"},
                "expirationDateTime": "",
                "comment": "{comment}",
                "customFields": {
                    "paySourcesFilter": "qw",
                    "themeCode": "Yvan-YKaSh",
                },
            },
            headers=self.P2P_QIWI_HEADERS,
        )

        self.QIWI_TO_WALLET: WrappedRequestPayload = WrappedRequestPayload(
            json={
                "id": str(int(time.time() * 1000)),
                "sum": {"amount": "", "currency": ""},
                "paymentMethod": {"type": "Account", "accountId": "643"},
                "comment": "",
                "fields": {"account": ""},
            },
            headers=self.DEFAULT_QIWI_HEADERS,
        )
        self.COMMISSION_DATA: WrappedRequestPayload = WrappedRequestPayload(
            json={
                "account": "",
                "paymentMethod": {"type": "Account", "accountId": "643"},
                "purchaseTotals": {"total": {"amount": "", "currency": "643"}},
            },
            headers=self.DEFAULT_QIWI_HEADERS,
        )
        self.DEFAULT_LIMIT_TYPES = [
            "TURNOVER",
            "REFILL",
            "PAYMENTS_P2P",
            "PAYMENTS_PROVIDER_INTERNATIONALS",
            "PAYMENTS_PROVIDER_PAYOUT",
            "WITHDRAW_CASH",
        ]
