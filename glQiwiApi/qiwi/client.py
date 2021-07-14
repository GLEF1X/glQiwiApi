"""
Gracefully and lightweight wrapper to deal with QIWI API
It's an open-source project so you always can improve the quality of code/API by
adding something of your own...
Easy to integrate to Telegram bot, which was written on aiogram or another async/sync library.

"""
from __future__ import annotations

import pathlib
import uuid
from abc import ABC
from contextlib import suppress
from copy import deepcopy
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Union, Optional, Any, Pattern, Match, Callable, cast, Iterable, Type

from glQiwiApi.core import RequestManager, constants
from glQiwiApi.core.core_mixins import ContextInstanceMixin, ToolsMixin
from glQiwiApi.core.web_hooks.dispatcher import Dispatcher
from glQiwiApi.ext.url_builder import WebhookURL
from glQiwiApi.qiwi.settings import QiwiRouter, QiwiKassaRouter, QiwiApiMethods
from glQiwiApi.types import (
    QiwiAccountInfo,
    Transaction,
    Statistic,
    Limit,
    Account,
    Balance,
    Identification,
    Sum,
    Card,
    Restriction,
    Commission,
    CrossRate,
    PaymentMethod,
    FreePaymentDetailsFields,
    PaymentInfo,
    OrderDetails,
    Bill,
    OptionalSum,
    P2PKeys,
    RefundBill,
    WebHookConfig,
    N
)
from glQiwiApi.types.basics import DEFAULT_CACHE_TIME
from glQiwiApi.utils import api_helper
from glQiwiApi.utils.errors import (
    RequestError,
    InvalidData
)


def _is_copy_signal(kwargs: Dict[Any, Any]) -> bool:
    try:
        return cast(bool, kwargs.pop("__copy_signal__"))
    except KeyError:
        return False


class BaseWrapper(ABC):
    """ Base wrapper class"""
    set_current: Callable[..., Any]

    def __init__(self, api_access_token: Optional[str] = None,
                 phone_number: Optional[str] = None,
                 secret_p2p: Optional[str] = None,
                 without_context: bool = False,
                 cache_time: Union[float, int] = DEFAULT_CACHE_TIME,  # 0 by default
                 validate_params: bool = False,
                 proxy: Any = None) -> None:
        """
        :param api_access_token: токен, полученный с https://qiwi.com/api
        :param phone_number: номер вашего телефона с +
        :param secret_p2p: секретный ключ, полученный с https://p2p.qiwi.com/
        :param without_context: bool, указывает, будет ли объект класса
         "глобальной" переменной или будет использована в async with контексте
        :param cache_time: Время кэширование запросов в секундах,
         по умолчанию 0, соответственно,
         запрос не будет использовать кэш по дефолту, максимальное время
         кэширование 60 секунд
        :param proxy: Прокси, которое будет использовано при создании сессии, может замедлить
            работу АПИ
        """
        if validate_params:
            self._validate_params(
                api_access_token=api_access_token,
                cache_time=cache_time,
                secret_p2p=secret_p2p,
                phone_number=phone_number,
                without_context=without_context
            )

        if isinstance(phone_number, str):
            self.phone_number = phone_number.replace('+', '')
            if self.phone_number.startswith('8'):
                self.phone_number = '7' + self.phone_number[1:]

        self._router: QiwiRouter = QiwiRouter()
        self._p2p_router: QiwiKassaRouter = QiwiKassaRouter()
        self._requests: RequestManager = RequestManager(
            without_context=without_context,
            messages=self._router.config.ERROR_CODE_NUMBERS,
            cache_time=cache_time,
            proxy=proxy
        )
        self.api_access_token = api_access_token
        self.secret_p2p = secret_p2p

        self._dispatcher: Optional[Dispatcher] = None

        # Method from ContextInstanceMixin
        self.set_current(self)

    @property
    def dp(self) -> Dispatcher:
        if not self._dispatcher:
            self._dispatcher = Dispatcher()
        return self._dispatcher

    @dp.setter
    def dp(self, other: Dispatcher) -> None:
        if not isinstance(other, Dispatcher):
            raise TypeError(f"Expected `Dispatcher`, got wrong type {type(other)}")
        self._dispatcher = other

    def _auth_token(
            self,
            headers: Dict[Any, Any],
            p2p: bool = False
    ) -> Dict[Any, Any]:
        """
        Make auth for API

        :param headers: dictionary
        :param p2p: boolean
        """
        headers['Authorization'] = headers['Authorization'].format(
            token=self.api_access_token if not p2p else self.secret_p2p
        )
        return headers

    @property
    def request_manager(self) -> RequestManager:
        """ Return :class:`RequestManager` """
        return self._requests

    @request_manager.setter
    def request_manager(self, manager: RequestManager) -> None:
        if not isinstance(manager, RequestManager):
            raise TypeError("Expected `RequestManager` hair, got %s" % type(manager))
        self._requests = manager

    @property
    def stripped_number(self) -> str:
        """returns number, in which the `+` sign is removed"""
        try:
            return self.phone_number.replace("+", "")
        except AttributeError:
            raise InvalidData("You should pass on phone number to execute this method") from None

    @staticmethod
    def _validate_params(api_access_token: Optional[str],
                         phone_number: Optional[str],
                         secret_p2p: Optional[str],
                         without_context: bool,
                         cache_time: Union[float, int]) -> None:
        """
        Validating all parameters by `isinstance` function or `regex`

        :param api_access_token:
        :param phone_number:
        :param without_context:
        :param cache_time:
        """
        import re

        if not isinstance(api_access_token, str):
            raise InvalidData("Invalid type of api_access_token parameter, required `string`,"
                              "you have passed %s" % type(api_access_token))
        if not isinstance(secret_p2p, str):
            raise InvalidData("Invalid type of secret_p2p parameter, required `string`,"
                              "you have passed %s" % type(secret_p2p))
        if not isinstance(without_context, bool):
            raise InvalidData("Invalid type of without_context parameter, required `bool`,"
                              "you have passed %s" % type(without_context))
        if not isinstance(cache_time, (float, int)):
            raise InvalidData("Invalid type of cache_time parameter, required `bool`,"
                              "you have passed %s" % type(cache_time))

        phone_number_pattern: Pattern[str] = re.compile(
            r"^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$"
        )
        match: Optional[Match[Any]] = re.fullmatch(phone_number_pattern, phone_number)

        if not match:
            raise InvalidData("Failed to verify parameter `phone_number` by regex. "
                              "Please, enter the correct phone number.")

    def __new__(cls: Type[N], api_access_token: Optional[str] = None,
                phone_number: Optional[str] = None,
                secret_p2p: Optional[str] = None,
                without_context: bool = False,
                cache_time: Union[float, int] = DEFAULT_CACHE_TIME,
                *args: Any, **kwargs: Any) -> N:
        if not isinstance(api_access_token, str) and not isinstance(secret_p2p, str):
            if not _is_copy_signal(kwargs):
                raise RuntimeError("Unable to initialize instance without tokens")

        return super().__new__(cls)  # type: ignore


class QiwiWrapper(BaseWrapper, ToolsMixin, ContextInstanceMixin["QiwiWrapper"]):
    """
    Delegates the work of QIWI API, webhooks, polling.
    Fast and versatile wrapper.

    """
    __slots__ = (
        'api_access_token',
        'phone_number',
        'secret_p2p',
        '_requests',
        '_router',
        '_p2p_router',
        '_dispatcher'
    )

    async def _register_webhook(self, web_url: Optional[str], txn_type: int = 2) -> WebHookConfig:
        """
        This method register a new webhook

        :param web_url: service url
        :param txn_type:  0 => incoming, 1 => outgoing, 2 => all
        :return: Active Hooks
        """
        response = await self.request_manager.send_request(
            "PUT", QiwiApiMethods.REG_WEBHOOK, self._router,
            headers=self._auth_token(self._router.default_headers),
            params={'hookType': 1, 'param': web_url, 'txnType': txn_type}
        )
        return WebHookConfig.parse_obj(response)

    async def get_current_webhook(self) -> WebHookConfig:
        """
        Список действующих (активных) обработчиков уведомлений,
         связанных с вашим кошельком, можно получить данным запросом.
        Так как сейчас используется только один тип хука - webhook,
         то в ответе содержится только один объект данных

        """
        response = await self.request_manager.send_request(
            "GET", QiwiApiMethods.GET_CURRENT_WEBHOOK, self._router,
            headers=self._auth_token(self._router.default_headers)
        )
        return WebHookConfig.parse_obj(response)

    async def _send_test_notification(self) -> Dict[Any, Any]:
        """
        Для проверки вашего обработчика webhooks используйте данный запрос.
        Тестовое уведомление отправляется на адрес, указанный при вызове
        register_webhook

        """
        return await self.request_manager.send_request("GET", QiwiApiMethods.SEND_TEST_NOTIFICATION, self._router,
                                                       headers=self._auth_token(self._router.default_headers))

    async def get_webhook_secret_key(self, hook_id: str) -> str:
        """
        Каждое уведомление содержит цифровую подпись сообщения,
         зашифрованную ключом.
        Для получения ключа проверки подписи используйте данный запрос.

        :param hook_id: UUID of webhook
        :return: Base64-закодированный ключ
        """
        resp = await self.request_manager.send_request("GET", QiwiApiMethods.GET_WEBHOOK_SECRET, self._router,
                                                       headers=self._auth_token(self._router.default_headers),
                                                       hook_id=hook_id)
        return cast(str, resp["key"])

    async def delete_current_webhook(self) -> Optional[Dict[str, str]]:
        """
        Method to delete webhook

        :return: Описание результата операции
        """
        try:
            hook = await self.get_current_webhook()
        except RequestError as ex:
            raise RequestError(
                message=" You didn't register any webhook to delete ",
                status_code='422',
                traceback_info=ex.traceback_info
            ) from None
        return await self.request_manager.send_request("DELETE", QiwiApiMethods.DELETE_CURRENT_WEBHOOK, self._router,
                                                       headers=self._auth_token(self._router.default_headers),
                                                       hook_id=hook.hook_id)

    async def change_webhook_secret(self, hook_id: str) -> str:
        """
        Для смены ключа шифрования уведомлений используйте данный запрос.

        :param hook_id: UUID of webhook
        :return: Base64-закодированный ключ
        """
        response = await self.request_manager.send_request("POST", QiwiApiMethods.CHANGE_WEBHOOK_SECRET, self._router,
                                                           headers=self._auth_token(self._router.default_headers),
                                                           hook_id=hook_id)
        return cast(str, response["key"])

    async def bind_webhook(
            self,
            url: Optional[Union[str, WebhookURL]] = None,
            transactions_type: int = 2,
            *,
            send_test_notification: bool = False,
            delete_old: bool = False
    ) -> Tuple[Optional[WebHookConfig], str]:
        """
        [NON-API] EXCLUSIVE method to register new webhook or get old

        :param url: service url
        :param transactions_type: 0 => incoming, 1 => outgoing, 2 => all
        :param send_test_notification:  test_qiwi will send
         you test webhook update
        :param delete_old: boolean, if True - delete old webhook

        :return: Tuple of Hook and Base64-encoded key
        """
        key: Optional[str] = None
        if isinstance(url, WebhookURL):
            url = url.render_as_string()

        if delete_old:
            with suppress(RequestError):
                await self.delete_current_webhook()

        try:
            # Try to register new webhook
            webhook = await self._register_webhook(url, transactions_type)
        except (RequestError, TypeError):
            # Catching exceptions, if webhook already was registered or TypeError because missing url to bind
            try:
                webhook = await self.get_current_webhook()
            except RequestError as ex:
                raise RequestError(
                    message="Ошибка при получении текущего конфига вебхука. Скорее всего вы не вызывали "
                            "метод bind_webhook, чтобы зарегистрировать вебхук"
                            " киви или не передали ссылку для его регистрации",
                    status_code=ex.status_code,
                    traceback_info=ex.traceback_info
                ) from None
            key = await self.get_webhook_secret_key(webhook.hook_id)
            return webhook, key

        if send_test_notification:
            await self._send_test_notification()

        if not isinstance(key, str):
            key = await self.get_webhook_secret_key(webhook.hook_id)

        return webhook, key

    @api_helper.override_error_messages(
        {
            404: {
                "message": "Введена неправильный номер карты, возможно, "
                           "карта на которую вы переводите заблокирована"
            }
        }
    )
    async def _detect_mobile_number(self, phone_number: str) -> str:
        """
        Метод для получения идентификатора телефона

        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#cards
        """
        headers = self._router.default_headers
        headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
        response = await self.request_manager.make_request(
            url="https://qiwi.com/mobile/detect.action",
            method="POST",
            headers=headers,
            data={'phone': phone_number}
        )
        return cast(str, response["message"])

    async def get_balance(self, *, account_number: int = 1) -> Sum:
        """Метод для получения баланса киви"""
        if account_number <= 0:
            raise ValueError("Account number cannot be negative")
        headers = self._auth_token(self._router.default_headers)
        response = await self.request_manager.send_request("GET", QiwiApiMethods.GET_BALANCE, self._router,
                                                           headers=headers, phone_number=self.phone_number)
        return Sum.parse_obj(response['accounts'][account_number - 1]['balance'])

    async def transactions(
            self,
            rows_num: int = 50,
            operation: str = 'ALL',
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Transaction]:
        """
        Метод для получения транзакций на счёту
        Более подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#payments_list

        Возможные значения параметра operation:
         - 'ALL'
         - 'IN'
         - 'OUT'
         - 'QIWI_CARD'

        :param rows_num: кол-во транзакций, которые вы хотите получить
        :param operation: Тип операций в отчете, для отбора.
        :param start_date:Начальная дата поиска платежей.
                            Используется только вместе с end_date.
        :param end_date: конечная дата поиска платежей.
                            Используется только вместе со start_date.
        """
        if rows_num > 50 or rows_num <= 0:
            raise InvalidData('Можно проверять не более 50 транзакций')
        headers = self._auth_token(self._router.default_headers)
        payload_data = api_helper.check_dates(
            start_date=start_date,
            end_date=end_date,
            payload_data={'rows': rows_num, 'operation': operation}
        )
        response = await self.request_manager.send_request("GET", QiwiApiMethods.TRANSACTIONS, self._router,
                                                           params=payload_data,
                                                           headers=headers, stripped_number=self.stripped_number)
        return api_helper.multiply_objects_parse((response.get('data'),), Transaction)  # type: ignore

    async def transaction_info(
            self,
            transaction_id: Union[str, int],
            transaction_type: str
    ) -> Transaction:
        """
        Метод для получения полной информации о транзакции\n
        Подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#txn_info

        :param transaction_id: номер транзакции
        :param transaction_type: тип транзакции, может быть только IN или OUT
        :return: Transaction object
        """
        headers = self._auth_token(self._router.default_headers)
        payload_data = {'type': transaction_type}
        response = await self.request_manager.send_request("GET", QiwiApiMethods.TRANSACTION_INFO, self._router,
                                                           headers=headers, params=payload_data,
                                                           transaction_id=transaction_id)
        return Transaction.parse_obj(response)

    async def check_restriction(self) -> List[Restriction]:
        """
        Метод для проверки ограничений на вашем киви кошельке\n
        Подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#restrictions

        :return: Список, где находиться словарь с ограничениями,
         если ограничений нет - возвращает пустой список
        """
        headers = self._auth_token(self._router.default_headers)
        response = await self.request_manager.send_request("GET", QiwiApiMethods.CHECK_RESTRICTION, self._router,
                                                           headers=headers, phone_number=self.phone_number)
        return api_helper.simple_multiply_parse(objects=response, model=Restriction)

    @property
    async def identification(self) -> Identification:
        """
        Функция, которая позволяет
        получить данные идентификации вашего кошелька
        Более подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#ident

        :return: Response object
        """
        headers = self._auth_token(self._router.default_headers)
        response = await self.request_manager.send_request("GET", QiwiApiMethods.GET_IDENTIFICATION, self._router,
                                                           headers=headers, phone_number=self.phone_number)
        return Identification.parse_obj(response)

    async def check_transaction(
            self,
            amount: Union[int, float],
            transaction_type: str = 'IN',
            sender: Optional[str] = None,
            rows_num: int = 50,
            comment: Optional[str] = None
    ) -> bool:
        """
        [ NON API METHOD ]
        Метод для проверки транзакции.\n
        Данный метод использует self.transactions(rows_num=rows_num)
        для получения платежей.\n
        Для небольшой оптимизации вы можете уменьшить rows_num задав его,
        однако это не гарантирует правильный результат
        Возможные значения параметра transaction_type:
         - 'IN'
         - 'OUT'
         - 'QIWI_CARD'


        :param amount: сумма платежа
        :param transaction_type: тип платежа
        :param sender: номер получателя
        :param rows_num: кол-во платежей, которое будет проверяться
        :param comment: комментарий, по которому будет проверяться транзакция
        :return: bool, есть ли такая транзакция в истории платежей
        """
        if transaction_type not in ['IN', 'OUT', 'QIWI_CARD']:
            raise InvalidData('Вы ввели неправильный метод транзакции')

        elif rows_num > 50 or rows_num <= 0:
            raise InvalidData('Можно проверять не более 50 транзакций')
        transactions = await self.transactions(rows_num=rows_num)
        return api_helper.check_transaction(
            transactions=transactions,
            transaction_type=transaction_type,
            comment=comment,
            amount=amount,
            sender=sender
        )

    async def get_limits(self) -> Dict[str, Limit]:
        """
        Функция для получения лимитов по счёту киви кошелька\n
        Возвращает лимиты по кошельку в виде списка,
        если лимита по определенной стране нет, то не включает его в список
        Подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#limits

        :return: Limit object of Limit(pydantic)
        """
        headers = self._auth_token(self._router.default_headers)
        payload = {}
        limit_types = self._router.config.LIMIT_TYPES
        for index, limit_type in enumerate(limit_types):
            payload['types[' + str(index) + ']'] = limit_type
        response = await self.request_manager.send_request("GET", QiwiApiMethods.GET_LIMITS, self._router,
                                                           headers=headers, params=payload,
                                                           stripped_number=self.stripped_number)
        return api_helper.parse_limits(response, Limit)

    async def get_list_of_cards(self) -> List[Card]:
        """
        Данный метод позволяет вам получить список ваших карт.

        """
        headers = self._auth_token(self._router.default_headers)
        response = await self.request_manager.send_request("GET", QiwiApiMethods.GET_LIST_OF_CARDS, self._router,
                                                           headers=headers)
        return api_helper.simple_multiply_parse(objects=response, model=Card)

    async def authenticate(
            self,
            birth_date: str,
            first_name: str,
            last_name: str,
            patronymic: str,
            passport: str,
            oms: Optional[str] = None,
            inn: Optional[str] = None,
            snils: Optional[str] = None
    ) -> Dict[Any, Any]:
        """
        Данный запрос позволяет отправить данные
        для идентификации вашего QIWI кошелька.
        Допускается идентифицировать не более 5 кошельков на одного владельца

        Для идентификации кошелька вы обязательно должны отправить ФИО,
        серию/номер паспорта и дату рождения.\n
        Если данные прошли проверку, то в ответе будет отображен
        ваш ИНН и упрощенная идентификация кошелька будет установлена.
        В случае если данные не прошли проверку,
        кошелек остается в статусе "Минимальный".

        :param birth_date: Дата рождения в виде строки формата 1998-02-11
        :param first_name: Ваше имя
        :param last_name: Ваша фамилия
        :param patronymic: Ваше отчество
        :param passport: Серия / Номер паспорта. Пример 4400111222
        :param oms:
        :param snils:
        :param inn:
        """

        payload = {
            "birthDate": birth_date,
            "firstName": first_name,
            "inn": inn,
            "lastName": last_name,
            "middleName": patronymic,
            "oms": oms,
            "passport": passport,
            "snils": snils
        }
        headers = self._auth_token(self._router.default_headers)
        return await self.request_manager.send_request("POST", QiwiApiMethods.AUTHENTICATE, self._router,
                                                       stripped_number=self.stripped_number,
                                                       headers=headers, data=self.request_manager.filter_dict(payload))

    @api_helper.override_error_messages({
        422: {
            "message": "Невозможно получить чек, из-за того, что "
                       "транзакция по такому айди не была проведена, "
                       "то есть произошла ошибка при проведении транзакции"
        }
    })
    async def get_receipt(
            self,
            transaction_id: Union[str, int],
            transaction_type: str,
            dir_path: Union[str, pathlib.Path, None] = None,
            file_name: Optional[str] = None
    ) -> Union[bytes, int]:
        """
        Метод для получения чека в формате байтов или файлом.\n
        Возможные значения transaction_type:
         - 'IN'
         - 'OUT'
         - 'QIWI_CARD'

        :param transaction_id: str or int, id транзакции,
         можно получить при вызове методе to_wallet, to_card
        :param transaction_type: тип транзакции может быть:
         'IN', 'OUT', 'QIWI_CARD'
        :param dir_path: путь к директории, куда вы хотите сохранить чек,
         если не указан, возвращает байты
        :param file_name: Имя файла без формата. Пример: my_receipt
        :return: pdf файл в байтовом виде или номер записанных байтов
        """
        headers = self._auth_token(self._router.default_headers)
        data = {'type': transaction_type, 'format': 'PDF'}
        url = self._router.build_url(QiwiApiMethods.GET_RECEIPT, transaction_id=transaction_id)
        response = await self.request_manager.stream_content(url, "GET", params=data, headers=headers)
        return await api_helper.save_file(dir_path=dir_path, file_name=file_name, data=response)

    @property
    async def account_info(self) -> QiwiAccountInfo:
        """
        Метод для получения информации об аккаунте

        """
        headers = self._auth_token(self._router.default_headers)
        response = await self.request_manager.send_request(
            "GET", QiwiApiMethods.ACCOUNT_INFO, self._router, headers=headers
        )
        return QiwiAccountInfo.parse_obj(response)

    async def fetch_statistics(
            self,
            start_date: Union[datetime, timedelta],
            end_date: Union[datetime, timedelta],
            operation: str = 'ALL',
            sources: Optional[List[str]] = None
    ) -> Statistic:
        """
        Данный запрос используется для получения сводной статистики
        по суммам платежей за заданный период.\n
        Более подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#payments_list

        :param start_date: Начальная дата периода статистики.
         Обязательный параметр
        :param end_date: Конечная дата периода статистики.
         Обязательный параметр
        :param operation: Тип операций, учитываемых при подсчете статистики.
         Допустимые значения:
            ALL - все операции,
            IN - только пополнения,
            OUT - только платежи,
            QIWI_CARD - только платежи по картам QIWI (QVC, QVP).
            По умолчанию ALL.
        :param sources: Источники платежа, по которым вернутся данные.
            QW_RUB - рублевый счет кошелька,
            QW_USD - счет кошелька в долларах,
            QW_EUR - счет кошелька в евро,
            CARD - привязанные и непривязанные к кошельку банковские карты,
            MK - счет мобильного оператора. Если не указан,
            учитываются все источники платежа.
        """
        headers = self._auth_token(self._router.default_headers)
        # Raise exception if invalid value of start_date or end_date
        api_helper.check_dates_for_statistic_request(start_date=start_date, end_date=end_date)
        params = {
            'startDate': api_helper.datetime_to_str_in_iso(start_date),
            'endDate': api_helper.datetime_to_str_in_iso(end_date),
            'operation': operation,
        }
        if sources:
            params.update({'sources': ' '.join(sources)})
        response = await self.request_manager.send_request("GET", QiwiApiMethods.FETCH_STATISTICS, self._router,
                                                           params=params, headers=headers,
                                                           stripped_number=self.stripped_number)
        return Statistic.parse_obj(response)

    async def list_of_balances(self) -> List[Account]:
        """
        Запрос выгружает текущие балансы счетов вашего QIWI Кошелька.
        Более подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#balances_list

        """
        headers = self._auth_token(self._router.default_headers)
        response = await self.request_manager.send_request("GET", QiwiApiMethods.LIST_OF_BALANCES, self._router,
                                                           headers=headers, stripped_number=self.stripped_number)
        return api_helper.simple_multiply_parse(cast(Iterable[Any], response.get('accounts')), Account)

    @api_helper.allow_response_code(201)
    async def create_new_balance(self, currency_alias: str) -> Optional[Dict[str, bool]]:
        """
        Запрос создает новый счет и баланс в вашем QIWI Кошельке

        :param currency_alias: Псевдоним нового счета
        :return: Возвращает значение из декоратора allow_response_code
         Пример результата, если запрос был проведен успешно: {"success": True}
        """
        headers = self._auth_token(self._router.default_headers)
        payload = {'alias': currency_alias}
        return await self.request_manager.send_request("POST", QiwiApiMethods.CREATE_NEW_BALANCE, self._router,
                                                       headers=headers, data=payload,
                                                       stripped_number=self.stripped_number)

    async def available_balances(self) -> List[Balance]:
        """
        Запрос отображает псевдонимы счетов,
        доступных для создания в вашем QIWI Кошельке
        Сигнатура объекта ответа:
        class Balance(BaseModel):
            alias: str
            currency: int

        """
        headers = self._auth_token(self._router.default_headers)
        response = await self.request_manager.send_request("GET", QiwiApiMethods.AVAILABLE_BALANCES, self._router,
                                                           headers=headers, stripped_number=self.stripped_number)
        return api_helper.simple_multiply_parse(objects=response, model=Balance)

    @api_helper.allow_response_code(status_code=204)
    async def set_default_balance(self, currency_alias: str) -> Any:
        """
        Запрос устанавливает для вашего QIWI Кошелька счет,
        баланс которого будет использоваться для фондирования
        всех платежей по умолчанию.
        Счет должен содержаться в списке счетов, получить список можно вызвав
        метод list_of_balances

        :param currency_alias: Псевдоним нового счета,
         можно получить из list_of_balances
        :return: Возвращает значение из декоратора allow_response_code
         Пример результата, если запрос был проведен успешно: {"success": True}
        """
        headers = self._auth_token(self._router.default_headers)
        return await self.request_manager.send_request("PATCH", QiwiApiMethods.SET_DEFAULT_BALANCE, self._router,
                                                       headers=headers, json={'defaultAccount': True},
                                                       stripped_number=self.stripped_number,
                                                       currency_alias=currency_alias)

    @property
    def transaction_handler(self):
        """
        Handler manager for default QIWI transactions,
        you can pass on lambda filter, if you want,
        but it must to return a boolean

        """
        return self.dp.transaction_handler_wrapper

    @property
    def bill_handler(self):
        """
        Handler manager for P2P bills,
        you can pass on lambda filter, if you want
        But it must to return a boolean

        """
        return self.dp.bill_handler_wrapper

    async def to_wallet(
            self,
            to_number: str,
            trans_sum: Union[str, float, int],
            currency: str = '643',
            comment: str = '+comment+') -> str:
        """
        Метод для перевода денег на другой кошелек\n
        Подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#p2p

        :param to_number: номер получателя
        :param trans_sum: кол-во денег, которое вы хотите перевести
        :param currency: особенный код валюты
        :param comment: комментарий к платежу
        """
        data = api_helper.set_data_to_wallet(
            data=deepcopy(self._router.config.QIWI_TO_WALLET),
            to_number=to_number,
            trans_sum=trans_sum,
            currency=currency,
            comment=comment
        )
        data.headers = self._auth_token(headers=data.headers)
        response = await self.request_manager.send_request("POST", QiwiApiMethods.TO_WALLET, self._router,
                                                           json=data.json, headers=data.headers)
        return cast(str, response['transaction']['id'])

    async def to_card(self, trans_sum: Union[float, int], to_card: str) -> Optional[str]:
        """
        Метод для отправки средств на карту.
        Более подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/#cards

        :param trans_sum: сумма перевода
        :param to_card: номер карты получателя
        :return:
        """
        data = api_helper.parse_card_data(
            default_data=self._router.config.QIWI_TO_CARD,
            to_card=to_card,
            trans_sum=trans_sum,
            auth_maker=self._auth_token
        )
        privat_card_id = await self._detect_card_number(card_number=to_card)
        response = await self.request_manager.send_request("POST", QiwiApiMethods.TO_CARD, self._router,
                                                           headers=data.headers, json=data.json,
                                                           privat_card_id=privat_card_id)
        return response.get('id')

    async def _detect_card_number(self, card_number: str) -> str:
        """
        Метод для получения идентификатора карты

        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#cards
        """
        headers = deepcopy(self._router.config.DEFAULT_QIWI_HEADERS)
        headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
        response = await self.request_manager.make_request(
            'https://qiwi.com/card/detect.action', "POST", headers=headers, data={'cardNumber': card_number}
        )
        return cast(str, response["message"])

    async def commission(self, to_account: str, pay_sum: Union[int, float]) -> Commission:
        """
        Возвращается полная комиссия QIWI Кошелька
        за платеж в пользу указанного провайдера
        с учетом всех тарифов по заданному набору платежных реквизитов.

        :param to_account: номер карты или киви кошелька
        :param pay_sum: сумма, за которую вы хотите узнать комиссию
        :return: Commission object
        """
        payload, special_code = api_helper.parse_commission_request_payload(
            default_data=self._router.config.COMMISSION_DATA,
            auth_maker=self._auth_token,
            to_account=to_account,
            pay_sum=pay_sum
        )
        code: str = special_code or await self._detect_card_number(to_account)
        response = await self.request_manager.send_request("POST", QiwiApiMethods.COMMISSION, self._router,
                                                           headers=payload.headers, json=payload.json,
                                                           special_code=code)
        return Commission.parse_obj(response)

    async def get_cross_rates(self) -> List[CrossRate]:
        """
        Метод возвращает текущие курсы и кросс-курсы валют КИВИ Банка.

        """
        response = await self.request_manager.send_request("GET", QiwiApiMethods.GET_CROSS_RATES, self._router)
        return api_helper.simple_multiply_parse(objects=response["result"], model=CrossRate)

    async def payment_by_payment_details(
            self,
            payment_sum: Sum,
            payment_method: PaymentMethod,
            fields: FreePaymentDetailsFields,
            payment_id: Optional[str] = None
    ) -> PaymentInfo:
        """
        Оплата услуг коммерческих организаций по их банковским реквизитам.

        :param payment_id: id платежа, если не передается, используется
         uuid4
        :param payment_sum: объект Sum, в котором указывается сумма платежа
        :param payment_method: метод платежа
        :param fields: Набор реквизитов платежа
        """
        payload = {
            "id": payment_id if isinstance(payment_id, str) else str(
                uuid.uuid4()
            ),
            "sum": payment_sum.dict(),
            "paymentMethod": payment_method.dict(),
            "fields": fields.dict()
        }
        response = await self.request_manager.send_request("POST", QiwiApiMethods.SPECIAL_PAYMENT, self._router,
                                                           headers=self._router.default_headers, json=payload)
        return PaymentInfo.parse_obj(response)

    async def buy_qiwi_master(self) -> PaymentInfo:
        """
        Метод для покупки пакета QIWI Мастер

        Для вызова методов API вам потребуется токен API QIWI Wallet
        с разрешениями на следующие действия:

        1. Управление виртуальными картами,
        2. Запрос информации о профиле кошелька,
        3. Просмотр истории платежей,
        4. Проведение платежей без SMS.

        Эти права вы можете выбрать при создании нового апи токена,
        чтобы пользоваться апи QIWI Master
        """
        payload = api_helper.qiwi_master_data(self.stripped_number, self._router.config.QIWI_MASTER)
        response = await self.request_manager.send_request("POST", QiwiApiMethods.BUY_QIWI_MASTER, self._router,
                                                           headers=self._auth_token(self._router.default_headers),
                                                           json=payload)
        return PaymentInfo.parse_obj(response)

    async def __pre_qiwi_master_request(self, card_alias: str = 'qvc-cpa') -> OrderDetails:
        """
        Метод для выпуска виртуальной карты QIWI Мастер

        :param card_alias: Тип карты
        :return: OrderDetails
        """
        response = await self.request_manager.send_request("POST", QiwiApiMethods.PRE_QIWI_REQUEST, self._router,
                                                           headers=self._auth_token(self._router.default_headers),
                                                           json={"cardAlias": card_alias},
                                                           stripped_number=self.stripped_number)
        return OrderDetails.parse_obj(response)

    async def _confirm_qiwi_master_request(self, card_alias: str = 'qvc-cpa') -> OrderDetails:
        """
        Подтверждение заказа выпуска карты

        :param card_alias: Тип карты
        :return: OrderDetails
        """
        details = await self.__pre_qiwi_master_request(card_alias)
        response = await self.request_manager.send_request("PUT", QiwiApiMethods.CONFIRM_QIWI_MASTER, self._router,
                                                           headers=self._auth_token(self._router.default_headers),
                                                           stripped_number=self.stripped_number,
                                                           order_id=details.order_id)
        return OrderDetails.parse_obj(response)

    async def __buy_new_qiwi_card(self, **kwargs: Any) -> Optional[OrderDetails]:
        """
        Покупка карты, если она платная

        :param kwargs:
        :return: OrderDetails
        """
        kwargs.update(data=self._router.config.QIWI_MASTER)
        payload = api_helper.new_card_data(**kwargs)
        response = await self.request_manager.send_request("POST", QiwiApiMethods.BUY_QIWI_CARD, self._router,
                                                           json=payload,
                                                           headers=self._auth_token(self._router.default_headers))
        return OrderDetails.parse_obj(response)

    async def issue_qiwi_master_card(self, card_alias: str = 'qvc-cpa') -> Optional[OrderDetails]:
        """
        Выпуск новой карты, используя Qiwi Master API

        При выпуске карты производиться 3, а возможно 3 запроса,
        а именно по такой схеме:
            - __pre_qiwi_master_request - данный метод создает заявку
            - _confirm_qiwi_master_request - подтверждает выпуск карты
            - __buy_new_qiwi_card - покупает новую карту,
              если такая карта не бесплатна


        Подробная документация:

        https://developer.qiwi.com/ru/qiwi-wallet-personal/#qiwi-master-issue-card

        :param card_alias: Тип карты
        :return: OrderDetails
        """
        pre_response = await self._confirm_qiwi_master_request(card_alias)
        if pre_response.status == 'COMPLETED':
            return pre_response
        return await self.__buy_new_qiwi_card(ph_number=self.stripped_number, order_id=pre_response.order_id)

    async def _cards_qiwi_master(self) -> Dict[Any, Any]:
        """
        Метод для получение списка всех ваших карт QIWI Мастер

        """
        return await self.request_manager.send_request("GET", QiwiApiMethods.CARDS_QIWI_MASTER, self._router,
                                                       headers=self._auth_token(self._router.default_headers))

    async def reject_p2p_bill(self, bill_id: str) -> Bill:
        """
        Метод для отмены транзакции.

        :param bill_id: номер p2p транзакции
        :return: Bill obj
        """
        if not self.secret_p2p:
            raise InvalidData('Не задан p2p токен')
        data = deepcopy(self._p2p_router.config.P2P_DATA)
        headers = self._auth_token(data.headers, p2p=True)
        response = await self.request_manager.send_request("POST", QiwiApiMethods.REJECT_P2P_BILL, self._p2p_router,
                                                           headers=headers, bill_id=bill_id)
        return Bill.parse_obj(response)

    async def check_p2p_bill_status(self, bill_id: str) -> str:
        """
        Метод для проверки статуса p2p транзакции.\n
        Возможные типы транзакции: \n
        WAITING	Счет выставлен, ожидает оплаты	\n
        PAID	Счет оплачен	\n
        REJECTED	Счет отклонен\n
        EXPIRED	Время жизни счета истекло. Счет не оплачен\n
        Более подробная документация:
        https://developer.qiwi.com/ru/p2p-payments/?shell#invoice-status

        :param bill_id: номер p2p транзакции
        :return: статус транзакции строкой
        """
        data = deepcopy(self._router.config.P2P_DATA)
        headers = self._auth_token(data.headers, p2p=True)
        response = await self.request_manager.send_request("GET", QiwiApiMethods.CHECK_P2P_BILL_STATUS,
                                                           self._p2p_router, headers=headers, bill_id=bill_id)
        return Bill.parse_obj(response).status.value

    async def create_p2p_bill(
            self,
            amount: Union[int, float],
            bill_id: Optional[str] = None,
            comment: Optional[str] = None,
            life_time: Optional[datetime] = None,
            theme_code: Optional[str] = None,
            pay_source_filter: Optional[List[str]] = None
    ) -> Bill:
        """
        Метод для выставление p2p счёта.
        Надежный способ для интеграции.
        Параметры передаются server2server с использованием авторизации.
        Возможные значения pay_source_filter:
          - 'qw'
          - 'card'
          - 'mobile'

        :param amount: сумма платежа
        :param bill_id: уникальный номер транзакции, если не передан,
         генерируется автоматически,
        :param life_time: дата, до которой счет будет доступен для оплаты.
        :param comment: комментарий к платежу
        :param theme_code: специальный код темы
        :param pay_source_filter: При открытии формы будут отображаться
         только указанные способы перевода
        """
        if not isinstance(bill_id, (str, int)):
            bill_id = str(uuid.uuid4())
        _life_time = api_helper.datetime_to_str_in_iso(constants.DEFAULT_BILL_TIME if not life_time else life_time)
        data = deepcopy(self._p2p_router.config.P2P_DATA)
        headers = self._auth_token(data.headers, p2p=True)
        payload = api_helper.set_data_p2p_create(data, amount, str(_life_time), comment, theme_code, pay_source_filter)
        response = await self.request_manager.send_request("PUT", QiwiApiMethods.CREATE_P2P_BILL, self._p2p_router,
                                                           headers=headers, json=payload, bill_id=bill_id)
        return Bill.parse_obj(response)

    async def get_bills(self, rows_num: int, bill_statuses: str = "READY_FOR_PAY") -> List[Bill]:
        """
        Метод получения списка неоплаченных счетов вашего кошелька.
        Список строится в обратном хронологическом порядке.
        По умолчанию, список разбивается на страницы по 50 элементов в каждой,
        но вы можете задать другое количество элементов (не более 50).
        В запросе можно использовать фильтры по времени выставления счета,
        начальному идентификатору счета.
        """
        headers = self._auth_token(self._router.default_headers)
        if rows_num > 50:
            raise InvalidData('Можно получить не более 50 счетов')

        params = {
            'rows': rows_num,
            'statuses': bill_statuses
        }
        response = await self.request_manager.send_request("GET", QiwiApiMethods.GET_BILLS, self._router,
                                                           headers=headers, params=params)
        return api_helper.simple_multiply_parse(response["bills"], Bill)

    async def refund_bill(
            self,
            bill_id: Union[str, int],
            refund_id: Union[str, int],
            json_bill_data: Union[OptionalSum, Dict[str, Union[str, int]]]
    ) -> RefundBill:
        """
        Метод позволяет сделать возврат средств по оплаченному счету.
        в JSON-теле запроса параметра json_bill_data:\n
         amount.value - сумма возврата. \n
         amount.currency - валюта возврата.
        Может быть словарем или объектом OptionalSum\n
         Пример словаря: {
        "amount": {
            "currency": "RUB",
            "value": 1
            }
        }

        :param bill_id: уникальный идентификатор счета в системе мерчанта
        :param refund_id: уникальный идентификатор возврата в системе мерчанта.
        :param json_bill_data:
        :return: RefundBill object
        """
        headers = self._auth_token(self._router.default_headers, p2p=True)
        json = json_bill_data if isinstance(json_bill_data, dict) else json_bill_data.json()
        response = await self.request_manager.send_request("PUT", QiwiApiMethods.REFUND_BILL, self._router,
                                                           headers=headers, json=json,
                                                           refund_id=refund_id, bill_id=bill_id)
        return RefundBill.parse_obj(response)

    async def create_p2p_keys(
            self,
            key_pair_name: str,
            server_notification_url: Optional[str] = None) -> P2PKeys:
        """
        Метод создает новые p2p ключи

        :param key_pair_name: Название пары токенов P2P (произвольная строка)
        :param server_notification_url: url для вебхуков, необязательный
         параметр
        """
        headers = self._auth_token(self._router.default_headers, p2p=True)
        data = {'keysPairName': key_pair_name, 'serverNotificationsUrl': server_notification_url}
        response = await self.request_manager.send_request("POST", QiwiApiMethods.CREATE_P2P_KEYS, self._router,
                                                           headers=headers, json=data)
        return P2PKeys.parse_obj(response)
