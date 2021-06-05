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
from copy import deepcopy
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Union, Optional, Any, MutableMapping, Pattern, Match, Callable

from glQiwiApi.core import RequestManager
from glQiwiApi.core.core_mixins import ContextInstanceMixin, ToolsMixin
from glQiwiApi.core.web_hooks.dispatcher import Dispatcher
from glQiwiApi.qiwi.settings import QiwiRouter, QiwiKassaRouter
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
    WebHookConfig
)
from glQiwiApi.types.basics import DEFAULT_CACHE_TIME
from glQiwiApi.utils import basics as api_helper
from glQiwiApi.utils.exceptions import (
    InvalidCardNumber,
    RequestError,
    InvalidData
)


def _is_copy_signal(kwargs: dict):
    try:
        return kwargs.pop("__copy_signal__")
    except KeyError:
        return False


class BaseWrapper(ABC):
    """ Base wrapper class"""
    set_current: Callable

    def __init__(self, api_access_token: Optional[str] = None,
                 phone_number: Optional[str] = None,
                 secret_p2p: Optional[str] = None,
                 without_context: bool = False,
                 cache_time: Union[float, int] = DEFAULT_CACHE_TIME,
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

        self.dispatcher = Dispatcher(loop=api_helper.take_event_loop())

        # Method from ContextInstanceMixin
        self.set_current(self)  # pragma: no cover

    def _auth_token(
            self,
            headers: MutableMapping,
            p2p: bool = False
    ) -> MutableMapping:
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
    def request_manager(self, manager: RequestManager):
        if not isinstance(manager, RequestManager):
            raise TypeError("Expected `RequestManager` hair, got %s" % type(manager))
        self._requests = manager

    @property
    def stripped_number(self) -> str:
        """returns number, in which the `+` sign is removed"""
        try:
            return self.phone_number.replace("+", "")
        except AttributeError:
            raise InvalidData(
                "You should pass on phone number to execute this method"
            ) from None

    @staticmethod
    def _validate_params(api_access_token: Optional[str],
                         phone_number: Optional[str],
                         secret_p2p: Optional[str],
                         without_context: bool,
                         cache_time: Union[float, int]):
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

    def __new__(cls, api_access_token: Optional[str] = None,
                phone_number: Optional[str] = None,
                secret_p2p: Optional[str] = None,
                without_context: bool = False,
                cache_time: Union[float, int] = DEFAULT_CACHE_TIME,
                *args, **kwargs):
        if not isinstance(api_access_token, str) and not isinstance(secret_p2p, str):
            if not _is_copy_signal(kwargs):
                raise RuntimeError("Cannot initialize an instance without any tokens")

        return super().__new__(cls)


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
        'dispatcher'
    )

    async def _register_webhook(
            self,
            web_url: Optional[str],
            txn_type: int = 2
    ) -> WebHookConfig:
        """
        This method register a new webhook

        :param web_url: service url
        :param txn_type:  0 => incoming, 1 => outgoing, 2 => all
        :return: Active Hooks
        """
        url = self._router.build_url("REG_WEBHOOK")
        async for response in self._requests.fast().fetch(
                url=url,
                method='PUT',
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                params={
                    'hookType': 1,
                    'param': web_url,
                    'txnType': txn_type
                },
                get_json=True
        ):
            return WebHookConfig.parse_obj(response.response_data)

    async def get_current_webhook(self) -> WebHookConfig:
        """
        Список действующих (активных) обработчиков уведомлений,
         связанных с вашим кошельком, можно получить данным запросом.
        Так как сейчас используется только один тип хука - webhook,
         то в ответе содержится только один объект данных

        """
        url = self._router.build_url("GET_CURRENT_WEBHOOK")
        async for response in self._requests.fast().fetch(
                url=url,
                method='GET',
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                get_json=True
        ):
            return WebHookConfig.parse_obj(response.response_data)

    async def _send_test_notification(self) -> Dict[str, str]:
        """
        Для проверки вашего обработчика webhooks используйте данный запрос.
        Тестовое уведомление отправляется на адрес, указанный при вызове
        register_webhook

        """
        url = self._router.build_url("SEND_TEST_NOTIFICATION")
        async for response in self._requests.fast().fetch(
                url=url,
                method='GET',
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                get_json=True
        ):
            return response.response_data

    async def get_webhook_secret_key(self, hook_id: str) -> str:
        """
        Каждое уведомление содержит цифровую подпись сообщения,
         зашифрованную ключом.
        Для получения ключа проверки подписи используйте данный запрос.

        :param hook_id: UUID of webhook
        :return: Base64-закодированный ключ
        """
        url = self._router.build_url(
            "GET_WEBHOOK_SECRET",
            hook_id=hook_id
        )
        async for response in self._requests.fast().fetch(
                url=url,
                method='GET',
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                get_json=True
        ):
            return response.response_data.get('key')

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
                json_info=ex.json()
            ) from None

        url = self._router.build_url(
            "DELETE_CURRENT_WEBHOOK",
            hook_id=hook.hook_id
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                method='DELETE',
                get_json=True
        ):
            return response.response_data

    async def change_webhook_secret(self, hook_id: str) -> str:
        """
        Для смены ключа шифрования уведомлений используйте данный запрос.

        :param hook_id: UUID of webhook
        :return: Base64-закодированный ключ
        """
        url = self._router.build_url(
            "CHANGE_WEBHOOK_SECRET",
            hook_id=hook_id
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                method='POST',
                get_json=True
        ):
            return response.response_data.get('key')

    async def bind_webhook(
            self,
            url: Optional[str] = None,
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

        if delete_old:
            await self.delete_current_webhook()

        try:
            # Try to register new webhook
            webhook = await self._register_webhook(
                web_url=url,
                txn_type=transactions_type
            )
        except (RequestError, TypeError):
            # Catching exception, if webhook already was registered
            try:
                webhook = await self.get_current_webhook()
            except RequestError as ex:
                raise RequestError(
                    message="You didn't pass on url to register new hook "
                            "and you didn't have registered webhooks",
                    status_code="422",
                    json_info=ex.json()
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
    async def _detect_mobile_number(self, phone_number: str):
        """
        Метод для получения идентификатора телефона

        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#cards
        """
        headers = deepcopy(self._router.config.DEFAULT_QIWI_HEADERS)
        headers.update(
            {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )
        async for response in self._requests.fetch(
                url='https://qiwi.com/mobile/detect.action',
                headers=headers,
                method='POST',
                data={
                    'phone': phone_number
                },
                get_json=True
        ):
            return response.response_data.get('message')

    async def get_balance(self) -> Sum:
        """Метод для получения баланса киви"""
        if not isinstance(self.phone_number, str):
            raise InvalidData(
                "Для вызова этого метода вы должны передать номер кошелька"
            )

        headers = self._auth_token(deepcopy(
            self._router.config.DEFAULT_QIWI_HEADERS
        ))
        url = self._router.build_url(
            "GET_BALANCE",
            phone_number=self.phone_number
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=headers,
                method='GET',
                get_json=True
        ):
            return Sum.parse_obj(
                response.response_data['accounts'][0]['balance']
            )

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

        headers = self._auth_token(deepcopy(
            self._router.config.DEFAULT_QIWI_HEADERS
        ))

        payload_data = api_helper.check_dates(
            start_date=start_date,
            end_date=end_date,
            payload_data={
                'rows': rows_num,
                'operation': operation
            }
        )
        url = self._router.build_url(
            "TRANSACTIONS",
            stripped_number=self.stripped_number
        )

        async for response in self._requests.fast().fetch(
                url=url,
                params=payload_data,
                headers=headers,
                method='GET',
                get_json=True
        ):
            return api_helper.multiply_objects_parse(
                lst_of_objects=(response.response_data.get('data'),),
                model=Transaction
            )

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
        headers = self._auth_token(deepcopy(
            self._router.config.DEFAULT_QIWI_HEADERS
        ))
        payload_data = {
            'type': transaction_type
        }
        url = self._router.build_url(
            "TRANSACTION_INFO",
            transaction_id=transaction_id
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=headers,
                params=payload_data,
                method='GET',
                get_json=True
        ):
            return Transaction.parse_obj(response.response_data)

    async def check_restriction(self) -> List[Restriction]:
        """
        Метод для проверки ограничений на вашем киви кошельке\n
        Подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#restrictions

        :return: Список, где находиться словарь с ограничениями,
         если ограничений нет - возвращает пустой список
        """
        if not isinstance(self.phone_number, str):
            raise InvalidData(
                "Для вызова этого метода вы должны передать номер кошелька"
            )
        headers = self._auth_token(deepcopy(
            self._router.config.DEFAULT_QIWI_HEADERS
        ))
        url = self._router.build_url(
            "CHECK_RESTRICTION",
            phone_number=self.phone_number
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=headers,
                method='GET',
                get_json=True
        ):
            return api_helper.simple_multiply_parse(
                lst_of_objects=response.response_data,
                model=Restriction
            )

    @property
    async def identification(self) -> Identification:
        """
        Функция, которая позволяет
        получить данные идентификации вашего кошелька
        Более подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#ident

        :return: Response object
        """
        if not isinstance(self.phone_number, str):
            raise InvalidData(
                "Для вызова этого метода вы должны передать номер кошелька"
            )

        headers = self._auth_token(deepcopy(
            self._router.config.DEFAULT_QIWI_HEADERS
        ))
        url = self._router.build_url(
            "GET_IDENTIFICATION",
            phone_number=self.phone_number
        )
        async for response in self._requests.fast().fetch(
                url=url,
                method='GET',
                headers=headers,
                get_json=True
        ):
            return Identification.parse_obj(response.response_data)

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
        headers = self._auth_token(deepcopy(
            self._router.config.DEFAULT_QIWI_HEADERS
        ))

        payload = {}
        limit_types = self._router.config.LIMIT_TYPES
        for index, limit_type in enumerate(limit_types):
            payload['types[' + str(index) + ']'] = limit_type
        url = self._router.build_url(
            "GET_LIMITS",
            stripped_number=self.stripped_number
        )
        async for response in self._requests.fast().fetch(
                url=url,
                get_json=True,
                headers=headers,
                params=payload,
                method='GET'
        ):
            return api_helper.parse_limits(response, Limit)

    async def get_list_of_cards(self) -> List[Card]:
        """
        Данный метод позволяет вам получить список ваших карт.

        """
        headers = self._auth_token(
            deepcopy(self._router.config.DEFAULT_QIWI_HEADERS)
        )
        async for response in self._requests.fast().fetch(
                url=self._router.build_url("GET_LIST_OF_CARDS"),
                method='GET',
                headers=headers,
                get_json=True
        ):
            return api_helper.simple_multiply_parse(
                lst_of_objects=response.response_data,
                model=Card
            )

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
    ) -> Optional[Dict[str, bool]]:
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
        headers = self._auth_token(
            deepcopy(self._router.config.DEFAULT_QIWI_HEADERS)
        )
        url = self._router.build_url(
            "AUTHENTICATE",
            stripped_number=self.stripped_number
        )
        async for response in self._requests.fast().fetch(
                url=url,
                data=self._requests.filter_dict(payload),
                headers=headers,
                get_json=True
        ):
            if response.ok and response.status_code == 200:
                return {'success': True}

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
            dir_path: Union[str, pathlib.Path] = None,
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
        headers = self._auth_token(deepcopy(
            self._router.config.DEFAULT_QIWI_HEADERS
        ))

        data = {
            'type': transaction_type,
            'format': 'PDF'
        }
        url = self._router.build_url(
            "GET_RECEIPT", transaction_id=transaction_id
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=headers,
                method='GET',
                params=data,
                get_bytes=True
        ):
            if not isinstance(
                    dir_path, (str, pathlib.Path)
            ) or not isinstance(file_name, str):
                return response.response_data

            return await api_helper.save_file(
                dir_path=dir_path, file_name=file_name,
                data=response.response_data
            )

    @property
    async def account_info(self) -> QiwiAccountInfo:
        """
        Метод для получения информации об аккаунте

        """
        headers = self._auth_token(deepcopy(
            self._router.config.DEFAULT_QIWI_HEADERS
        ))
        async for response in self._requests.fast().fetch(
                url=self._router.build_url("ACCOUNT_INFO"),
                headers=headers,
                method='GET',
                get_json=True
        ):
            return QiwiAccountInfo.parse_obj(response.response_data)

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
        headers = self._auth_token(
            deepcopy(self._router.config.DEFAULT_QIWI_HEADERS)
        )
        # Raise exception if invalid value of start_date or end_date
        api_helper.check_dates_for_statistic_request(
            start_date=start_date,
            end_date=end_date
        )
        params = {
            'startDate': api_helper.datetime_to_str_in_iso(start_date),
            'endDate': api_helper.datetime_to_str_in_iso(end_date),
            'operation': operation,
        }

        if sources:
            params.update({'sources': ' '.join(sources)})

        url = self._router.build_url(
            "FETCH_STATISTICS",
            stripped_number=self.stripped_number
        )
        async for response in self._requests.fast().fetch(
                url=url,
                params=params,
                headers=headers,
                get_json=True,
                method='GET'
        ):
            return Statistic.parse_obj(response.response_data)

    async def list_of_balances(self) -> List[Account]:
        """
        Запрос выгружает текущие балансы счетов вашего QIWI Кошелька.
        Более подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#balances_list

        """
        url = self._router.build_url(
            "LIST_OF_BALANCES",
            stripped_number=self.stripped_number
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                method='GET',
                get_json=True
        ):
            return api_helper.simple_multiply_parse(
                response.response_data.get('accounts'), Account
            )

    @api_helper.allow_response_code(201)
    async def create_new_balance(
            self, currency_alias: str
    ) -> Optional[Dict[str, bool]]:
        """
        Запрос создает новый счет и баланс в вашем QIWI Кошельке

        :param currency_alias: Псевдоним нового счета
        :return: Возвращает значение из декоратора allow_response_code
         Пример результата, если запрос был проведен успешно: {"success": True}
        """
        headers = self._auth_token(deepcopy(
            self._router.config.DEFAULT_QIWI_HEADERS
        ))
        payload = {
            'alias': currency_alias
        }
        url = self._router.build_url(
            "CREATE_NEW_BALANCE",
            stripped_number=self.stripped_number
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=headers,
                data=payload,
                get_json=True
        ):
            return response.response_data

    async def available_balances(self) -> List[Balance]:
        """
        Запрос отображает псевдонимы счетов,
        доступных для создания в вашем QIWI Кошельке
        Сигнатура объекта ответа:
        class Balance(BaseModel):
            alias: str
            currency: int

        """
        url = self._router.build_url(
            "AVAILABLE_BALANCES",
            stripped_number=self.stripped_number
        )
        headers = self._auth_token(deepcopy(
            self._router.config.DEFAULT_QIWI_HEADERS
        ))
        async for response in self._requests.fast().fetch(
                url=url,
                headers=headers,
                method='GET',
                get_json=True
        ):
            return api_helper.simple_multiply_parse(
                lst_of_objects=response.response_data, model=Balance)

    @api_helper.allow_response_code(204)
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
        headers = self._auth_token(deepcopy(
            self._router.config.DEFAULT_QIWI_HEADERS
        ))
        url = self._router.build_url(
            "SET_DEFAULT_BALANCE",
            stripped_number=self.stripped_number,
            currency_alias=currency_alias
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=headers,
                method='PATCH',
                json={'defaultAccount': True},
                get_json=True
        ):
            return response

    @property
    def transaction_handler(self):
        """
        Handler manager for default QIWI transactions,
        you can pass on lambda filter, if you want,
        but it must to return a boolean

        """
        return self.dispatcher.transaction_handler_wrapper

    @property
    def bill_handler(self):
        """
        Handler manager for P2P bills,
        you can pass on lambda filter, if you want
        But it must to return a boolean

        """
        return self.dispatcher.bill_handler_wrapper

    async def to_wallet(
            self,
            to_number: str,
            trans_sum: Union[str, float, int],
            currency: str = '643',
            comment: str = '+comment+') -> Optional[str]:
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
        data.headers = self._auth_token(
            headers=data.headers
        )
        async for response in self._requests.fast().fetch(
                url=self._router.build_url("TO_WALLET"),
                json=data.json,
                headers=data.headers,
                get_json=True
        ):
            return response.response_data['transaction']['id']

    async def to_card(
            self,
            trans_sum: Union[float, int],
            to_card: str
    ) -> Optional[str]:
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
        async for response in self._requests.fast().fetch(
                url=self._router.build_url(
                    "TO_CARD", privat_card_id=privat_card_id
                ),
                headers=data.headers,
                json=data.json,
                get_json=True
        ):
            return response.response_data.get('id')

    async def _detect_card_number(self, card_number: str) -> str:
        """
        Метод для получения идентификатора карты

        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#cards
        """
        headers = deepcopy(self._router.config.DEFAULT_QIWI_HEADERS)
        headers.update(
            {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )
        async for response in self._requests.fetch(
                url='https://qiwi.com/card/detect.action',
                headers=headers,
                method='POST',
                data={
                    'cardNumber': card_number
                },
                get_json=True
        ):
            try:
                return response.response_data.get('message')
            except KeyError:
                raise InvalidCardNumber(
                    'Invalid card number or qiwi api is not response'
                ) from None

    async def commission(
            self,
            to_account: str,
            pay_sum: Union[int, float]
    ) -> Commission:
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
        if not isinstance(special_code, str):
            special_code = await self._detect_card_number(
                card_number=to_account
            )
        url = self._router.build_url("COMMISSION", special_code=special_code)
        async for response in self._requests.fast().fetch(
                url=url,
                headers=payload.headers,
                json=payload.json,
                get_json=True
        ):
            return Commission.parse_obj(response.response_data)

    async def get_cross_rates(self) -> List[CrossRate]:
        """
        Метод возвращает текущие курсы и кросс-курсы валют КИВИ Банка.

        """
        url = self._router.build_url("GET_CROSS_RATES")
        async for response in self._requests.fast().fetch(
                url=url,
                method='GET',
                get_json=True
        ):
            return api_helper.simple_multiply_parse(
                lst_of_objects=response.response_data.get("result"),
                model=CrossRate
            )

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
        :param payment_sum: обьект Sum, в котором указывается сумма платежа
        :param payment_method: метод платежа
        :param fields: Набор реквизитов платежа
        """
        url = self._router.build_url("SPECIAL_PAYMENT")
        headers = deepcopy(self._router.config.DEFAULT_QIWI_HEADERS)
        payload = {
            "id": payment_id if isinstance(payment_id, str) else str(
                uuid.uuid4()
            ),
            "sum": payment_sum.dict(),
            "paymentMethod": payment_method.dict(),
            "fields": fields.dict()
        }
        async for response in self._requests.fast().fetch(
                url=url,
                json=payload,
                headers=headers,
                get_json=True
        ):
            return PaymentInfo.parse_obj(response.response_data)

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
        url = self._router.build_url("BUY_QIWI_MASTER")
        payload = api_helper.qiwi_master_data(self.stripped_number,
                                              self._router.config.QIWI_MASTER)
        async for response in self._requests.fast().fetch(
                url=url,
                json=payload,
                method='POST',
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                get_json=True
        ):
            return PaymentInfo.parse_obj(response.response_data)

    async def __pre_qiwi_master_request(
            self,
            card_alias: str = 'qvc-cpa'
    ) -> OrderDetails:
        """
        Метод для выпуска виртуальной карты QIWI Мастер

        :param card_alias: Тип карты
        :return: OrderDetails
        """
        url = self._router.build_url(
            "PRE_QIWI_REQUEST",
            stripped_number=self.stripped_number
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                json={"cardAlias": card_alias},
                method='POST',
                get_json=True
        ):
            return OrderDetails.parse_obj(response.response_data)

    async def _confirm_qiwi_master_request(
            self,
            card_alias: str = 'qvc-cpa'
    ) -> OrderDetails:
        """
        Подтверждение заказа выпуска карты

        :param card_alias: Тип карты
        :return: OrderDetails
        """
        details = await self.__pre_qiwi_master_request(card_alias)
        url = self._router.build_url(
            "_CONFIRM_QIWI_MASTER",
            stripped_number=self.stripped_number,
            order_id=details.order_id
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                method='PUT',
                get_json=True
        ):
            return OrderDetails.parse_obj(response.response_data)

    async def __buy_new_qiwi_card(
            self,
            **kwargs
    ) -> Optional[OrderDetails]:
        """
        Покупка карты, если она платная

        :param kwargs:
        :return: OrderDetails
        """
        kwargs.update(data=self._router.config.QIWI_MASTER)
        url, payload = api_helper.new_card_data(**kwargs)
        async for response in self._requests.fast().fetch(
                url=url,
                json=payload,
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                get_json=True
        ):
            return OrderDetails.parse_obj(response.response_data)

    async def issue_qiwi_master_card(
            self,
            card_alias: str = 'qvc-cpa'
    ) -> Optional[OrderDetails]:
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
        return await self.__buy_new_qiwi_card(
            ph_number=self.stripped_number,
            order_id=pre_response.order_id
        )

    async def _cards_qiwi_master(self):
        """
        Метод для получение списка всех ваших карт QIWI Мастер

        """
        url = self._router.build_url("CARDS_QIWI_MASTER")
        async for response in self._requests.fast().fetch(
                url=url,
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                method='GET',
                get_json=True
        ):
            return response

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
        url = f'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}/reject'
        async for response in self._requests.fast().fetch(
                url=url,
                method='POST',
                headers=headers,
                get_json=True
        ):
            return Bill.parse_obj(response.response_data)

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
        if not self.secret_p2p:
            raise InvalidData('Не задан p2p токен')

        data = deepcopy(self._router.config.P2P_DATA)
        headers = self._auth_token(data.headers, p2p=True)
        url = self._p2p_router.build_url(
            "CHECK_P2P_BILL_STATUS",
            bill_id=bill_id
        )
        async for response in self._requests.fast().fetch(
                url=url,
                method='GET',
                headers=headers,
                get_json=True
        ):
            return Bill.parse_obj(response.response_data).status.value

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
        from glQiwiApi.core import constants

        if not self.secret_p2p:
            raise InvalidData('Не задан p2p токен')

        if not isinstance(bill_id, (str, int)):
            bill_id = str(uuid.uuid4())

        _life_time = api_helper.datetime_to_str_in_iso(
            constants.DEFAULT_BILL_TIME if not life_time else life_time
        )

        data = deepcopy(self._p2p_router.config.P2P_DATA)

        headers = self._auth_token(data.headers, p2p=True)

        payload = api_helper.set_data_p2p_create(
            wrapped_data=data,
            amount=amount,
            comment=comment,
            theme_code=theme_code,
            pay_source_filter=pay_source_filter,
            life_time=str(_life_time)
        )
        url = self._p2p_router.build_url(
            "CREATE_P2P_BILL",
            bill_id=bill_id
        )
        async for response in self._requests.fast().fetch(
                url=url,
                json=payload,
                headers=headers,
                method='PUT',
                get_json=True
        ):
            return Bill.parse_obj(response.response_data)

    async def get_bills(self, rows_num: int) -> List[Bill]:
        """
        Метод получения списка неоплаченных счетов вашего кошелька.
        Список строится в обратном хронологическом порядке.
        По умолчанию, список разбивается на страницы по 50 элементов в каждой,
        но вы можете задать другое количество элементов (не более 50).
        В запросе можно использовать фильтры по времени выставления счета,
        начальному идентификатору счета.
        """
        headers = self._auth_token(
            deepcopy(self._router.config.DEFAULT_QIWI_HEADERS)
        )
        if rows_num > 50:
            raise InvalidData('Можно получить не более 50 счетов')

        params = {
            'rows': rows_num,
            'statuses': 'READY_FOR_PAY'
        }
        async for response in self._requests.fast().fetch(
                url=self._router.build_url("GET_BILLS"),
                headers=headers,
                method='GET',
                params=params,
                get_json=True
        ):
            return api_helper.simple_multiply_parse(
                response.response_data.get("bills"), Bill
            )

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
        url = self._router.build_url(
            "REFUND_BILL",
            refund_id=refund_id,
            bill_id=bill_id
        )
        headers = self._auth_token(
            deepcopy(self._router.config.DEFAULT_QIWI_HEADERS), p2p=True
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=headers,
                method='PUT',
                json=json_bill_data if isinstance(
                    json_bill_data,
                    dict
                ) else json_bill_data.json(),
                get_json=True
        ):
            return RefundBill.parse_obj(response.response_data)

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
        url = self._router.build_url("CREATE_P2P_KEYS")
        headers = self._auth_token(
            deepcopy(self._router.config.DEFAULT_QIWI_HEADERS), p2p=True
        )
        data = {
            'keysPairName': key_pair_name,
            'serverNotificationsUrl': server_notification_url
        }
        async for response in self._requests.fast().fetch(
                url=url,
                headers=headers,
                json=data,
                get_json=True
        ):
            return P2PKeys.parse_obj(response.response_data)
