import functools
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Any, Union, Dict, List

from glQiwiApi.core.abstracts import AbstractRouter
from glQiwiApi.types import WrapperData
from glQiwiApi.utils.basics import check_api_method


@dataclass
class QiwiSettings:
    # Qiwi Wallet
    TO_CARD: str = '/sinap/api/v2/terms/{privat_card_id}'

    GET_BALANCE: str = '/funding-sources/v2/persons/{phone_number}/accounts'

    TRANSACTIONS: str = '/payment-history/v2/persons/{stripped_number}/payments'

    TO_WALLET: str = '/sinap/api/v2/terms/99/payments'

    TRANSACTION_INFO: str = '/payment-history/v1/transactions/{transaction_id}'

    CHECK_RESTRICTION: str = '/person-profile/v1/persons/{phone_number}/status/restrictions'

    GET_IDENTIFICATION: str = '/identification/v1/persons/{phone_number}/identification'

    GET_LIMITS: str = '/qw-limits/v1/persons/{stripped_number}/actual-limits'

    GET_LIST_OF_CARDS: str = '/cards/v1/cards'

    AUTHENTICATE: str = '/identification/v1/persons/{stripped_number}/identification'

    GET_BILLS: str = '/checkout-api/api/bill/search'

    GET_RECEIPT: str = '/payment-history/v1/transactions/{transaction_id}/cheque/file'

    COMMISSION: str = '/sinap/providers/{special_code}/onlineCommission'

    ACCOUNT_INFO: str = '/person-profile/v1/profile/current'

    FETCH_STATISTICS: str = '/payment-history/v2/persons/{stripped_number}/payments/total'

    LIST_OF_BALANCES: str = '/funding-sources/v2/persons/{stripped_number}/accounts'

    CREATE_NEW_BALANCE: str = '/funding-sources/v2/persons/{stripped_number}/accounts'

    AVAILABLE_BALANCES: str = '/funding-sources/v2/persons/{stripped_number}/accounts/offer'

    SET_DEFAULT_BALANCE: str = '/funding-sources/v2/persons/{stripped_number}/accounts/{currency_alias}'

    BUY_QIWI_MASTER: str = '/sinap/api/v2/terms/28004/payments'

    _CONFIRM_QIWI_MASTER: str = '/cards/v2/persons/{stripped_number}/orders/{order_id}/submit'

    CARDS_QIWI_MASTER: str = '/cards/v1/cards/?vas-alias=qvc-master'

    PRE_QIWI_REQUEST: str = '/cards/v2/persons/{number}/orders'

    GET_CROSS_RATES: str = '/sinap/crossRates'

    SPECIAL_PAYMENT: str = '/sinap/api/v2/terms/1717/payments'

    # Qiwi P2P
    CREATE_P2P_BILL: str = '/{bill_id}'
    CHECK_P2P_BILL_STATUS: str = '/{bill_id}'
    REJECT_P2P_BILL: str = '/{bill_id}/reject'
    REFUND_BILL: str = '/{bill_id}/refunds/{refund_id}'
    CREATE_P2P_KEYS: str = '/widgets-api/api/p2p/protected/keys/create'

    # Webhooks
    REG_WEBHOOK: str = '/payment-notifier/v1/hooks'

    GET_CURRENT_WEBHOOK: str = '/payment-notifier/v1/hooks/active'

    SEND_TEST_NOTIFICATION: str = '/payment-notifier/v1/hooks/test'

    GET_WEBHOOK_SECRET: str = '/payment-notifier/v1/hooks/{hook_id}/key'

    DELETE_CURRENT_WEBHOOK: str = '/payment-notifier/v1/hooks/{hook_id}'

    CHANGE_WEBHOOK_SECRET: str = '/payment-notifier/v1/hooks/{hook_id}/newkey'

    # Payload data
    DEFAULT_QIWI_HEADERS: Optional[Dict[str, Union[str, int]]] = None

    ERROR_CODE_NUMBERS: Optional[Dict[str, Union[str, int]]] = None

    P2P_QIWI_HEADERS: Optional[Dict[str, Union[str, int]]] = None

    def __init__(self, *args, **kwargs):
        self.DEFAULT_QIWI_HEADERS = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer {token}',
            'Host': 'edge.test_qiwi.com',
        }
        self.P2P_QIWI_HEADERS = {
            'Authorization': 'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        self.ERROR_CODE_NUMBERS = {
            "400": "Недостаточно средств для проведения операции",
            "401": "Неверный токен или истек срок действия токена API",
            "403": "Нет прав на данный запрос"
                   "(недостаточно разрешений у токена API)",
            "404": "Не найдена транзакция или "
                   "отсутствуют платежи с указанными признаками",
            "423": "Слишком много запросов, сервис временно недоступен",
            "422": "Неправильно указаны домен/подсеть/хост"
                   " веб-хука(в параметре new_url для URL веб-хука), "
                   "неправильно указаны тип хука или тип транзакции, "
                   "попытка создать хук при наличии уже созданного",
            "405": "Ошибка, связанная с типом запроса к апи,"
                   "обратитесь к разработчику или откройте issue",
            "500": "Внутренняя ошибка сервиса",
            "400_special_bad_proxy": "Ошибка, связанная с использованием прокси"
        }
        self.QIWI_MASTER = {
            "id": str(int(time.time() * 1000)),
            "sum": {
                "amount": 2999,
                "currency": "643"
            },
            "paymentMethod": {
                "type": "Account",
                "accountId": "643"
            },
            "comment": "test",
            "fields": {
                "account": "",
                "vas_alias": "qvc-master"
            }
        }

        for key, value in kwargs.items():
            setattr(self, key, value)
        for arg in args:
            setattr(self, arg, arg)

        self.LIMIT_TYPES = [
            'TURNOVER',
            'REFILL',
            'PAYMENTS_P2P',
            'PAYMENTS_PROVIDER_INTERNATIONALS',
            'PAYMENTS_PROVIDER_PAYOUT',
            'WITHDRAW_CASH'
        ]
        self.QIWI_TO_CARD.headers = self.DEFAULT_QIWI_HEADERS
        self.P2P_DATA.headers = self.DEFAULT_QIWI_HEADERS
        self.QIWI_TO_WALLET.headers = self.DEFAULT_QIWI_HEADERS
        self.COMMISSION_DATA.headers = self.DEFAULT_QIWI_HEADERS

    QIWI_TO_CARD: WrapperData = WrapperData(
        json={
            "id": str(int(time.time() * 1000)),
            "sum": {
                "amount": "", "currency": "643"
            },
            "paymentMethod": {
                "type": "Account", "accountId": "643"
            },
            "fields": {
                "account": ""
            }
        },
        headers=DEFAULT_QIWI_HEADERS
    )

    P2P_DATA: WrapperData = WrapperData(
        json={
            "amount": {
                "currency": "RUB",
                "value": "{amount}"
            },
            "expirationDateTime": "",
            "comment": "{comment}",
            "customFields": {
                "paySourcesFilter": "qw",
                "themeCode": "Yvan-YKaSh",
            }
        },

        headers=P2P_QIWI_HEADERS
    )

    QIWI_TO_WALLET: WrapperData = WrapperData(
        json={
            "id": str(int(time.time() * 1000)),
            "sum": {
                "amount": "",
                "currency": ""
            },
            "paymentMethod": {
                "type": "Account",
                "accountId": "643"
            },
            "comment": "",
            "fields": {
                "account": ""
            }
        },
        headers=DEFAULT_QIWI_HEADERS
    )

    LIMIT_TYPES: Optional[List[str]] = None

    COMMISSION_DATA: WrapperData = WrapperData(
        json={
            "account": "",
            "paymentMethod": {
                "type": "Account",
                "accountId": "643"
            },
            "purchaseTotals":
                {
                    "total":
                        {"amount": "",
                         "currency": "643"
                         }
                }},
        headers=DEFAULT_QIWI_HEADERS
    )

    QIWI_MASTER: Dict[str, Union[int, float, str]] = None


@lru_cache()
def get_settings() -> QiwiSettings:
    settings = QiwiSettings()
    return settings


class QiwiRouter(AbstractRouter):
    """Class, which deals with all methods, except p2p"""
    __head__ = "https://edge.qiwi.com"

    @functools.lru_cache()
    def build_url(self, api_method: str, **kwargs: Any) -> str:
        check_api_method(api_method)
        tail: str = getattr(self.config, api_method, None)
        pre_build_url = self.__head__ + tail
        return super()._format_url_kwargs(pre_build_url, **kwargs)

    def setup_config(self) -> Any:
        return get_settings()


class QiwiKassaRouter(QiwiRouter):
    """ QIWI P2P router"""
    __head__ = "https://api.qiwi.com/partner/bill/v1/bills"


__all__ = ('get_settings', "QiwiRouter", "QiwiKassaRouter")
