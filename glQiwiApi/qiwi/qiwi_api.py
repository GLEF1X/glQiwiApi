import asyncio
import logging
import uuid
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Union, Optional, Dict, List, Any, Tuple

import aiofiles
from aiohttp import web, ClientSession
from aiohttp.abc import AbstractAccessLogger

from glQiwiApi.core import (
    AbstractPaymentWrapper,
    RequestManager,
    ToolsMixin
)
from glQiwiApi.core.web_hooks import server, handler
from glQiwiApi.core.web_hooks.config import Path
from glQiwiApi.core.web_hooks.webhook_mixin import AccessLogger
from glQiwiApi.qiwi.basic_qiwi_config import (
    BASE_QIWI_URL, ERROR_CODE_NUMBERS,
    QIWI_TO_CARD, DEFAULT_QIWI_HEADERS,
    P2P_DATA, QIWI_TO_WALLET,
    COMMISSION_DATA, LIMIT_TYPES
)
from glQiwiApi.types import (
    QiwiAccountInfo,
    Transaction,
    Bill,
    BillError,
    Statistic,
    Limit,
    Account,
    Balance,
    Identification,
    Sum,
    Commission,
    OptionalSum,
    PaymentInfo,
    OrderDetails, WebHookConfig
)
from glQiwiApi.types.basics import DEFAULT_CACHE_TIME
from glQiwiApi.types.qiwi_types.bill import RefundBill
from glQiwiApi.utils import basics as api_helper
from glQiwiApi.utils.exceptions import (
    InvalidData,
    InvalidCardNumber,
    RequestError
)

DEFAULT_BILL_TIME = datetime.now() + timedelta(days=2)


class QiwiWrapper(AbstractPaymentWrapper, ToolsMixin):
    """
    Класс, реализующий обработку запросов к киви, удобен он тем,
    что не просто отдает json подобные объекты, а
    конвертирует ответ апи в pydantic модель.

    """

    __slots__ = (
        'api_access_token',
        'phone_number',
        'secret_p2p',
        '_requests',
    )

    def __init__(self, api_access_token: Optional[str] = None,
                 phone_number: Optional[str] = None,
                 secret_p2p: Optional[str] = None,
                 without_context: bool = False,
                 cache_time: Union[float, int] = DEFAULT_CACHE_TIME) -> None:
        """
        :param api_access_token: токен, полученный с https://qiwi.com/api
        :param phone_number: номер вашего телефона с +
        :param secret_p2p: секретный ключ, полученный с https://p2p.qiwi.com/
        :param without_context: bool, указывает будет ли объект класса
         "глобальной" переменной или будет использована в async with контексте
        :param cache_time: Время кэширование запросов в секундах,
         по умолчанию 0, соответственно,
         запрос не будет использовать кэш по дефолту, максимальное время
         кэширование 60 секунд
        """
        if isinstance(phone_number, str):
            self.phone_number = phone_number.replace('+', '')
            if self.phone_number.startswith('8'):
                self.phone_number = '7' + self.phone_number[1:]
        self._requests = RequestManager(
            without_context=without_context,
            messages=ERROR_CODE_NUMBERS,
            cache_time=cache_time
        )
        self.api_access_token = api_access_token
        self.secret_p2p = secret_p2p
        self.handler_manager = handler.HandlerManager(
            loop=asyncio.get_event_loop()
        )

    def _auth_token(self, headers: dict, p2p: bool = False) -> dict:
        headers['Authorization'] = headers['Authorization'].format(
            token=self.api_access_token if not p2p else self.secret_p2p
        )
        return headers

    @property
    def session(self) -> ClientSession:
        """Return aiohttp session object"""
        return self._requests.session

    @property
    def stripped_number(self) -> str:
        try:
            return self.phone_number.replace("+", "")
        except AttributeError:
            raise InvalidData(
                "You should pass on phone number to execute this method"
            ) from None

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
            default_data=QIWI_TO_CARD,
            to_card=to_card,
            trans_sum=trans_sum,
            auth_maker=self._auth_token
        )
        privat_card_id = await self._detect_card_number(card_number=to_card)
        base_url = BASE_QIWI_URL + '/sinap/api/v2/terms/' + privat_card_id
        async for response in self._requests.fast().fetch(
                url=base_url + '/payments',
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
        headers = deepcopy(DEFAULT_QIWI_HEADERS)
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
                }
        ):
            try:
                return response.response_data.get('message')
            except KeyError:
                raise InvalidCardNumber(
                    'Invalid card number or qiwi api is not response'
                ) from None

    async def _detect_mobile_number(self, phone_number: str):
        """
        Метод для получения идентификатора телефона

        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#cards
        """
        headers = deepcopy(DEFAULT_QIWI_HEADERS)
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
                }
        ):
            return response.response_data.get('message')

    async def get_balance(self) -> Sum:
        """Метод для получения баланса киви"""
        if not isinstance(self.phone_number, str):
            raise InvalidData(
                "Для вызова этого метода вы должны передать номер кошелька"
            )

        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        url = BASE_QIWI_URL + '/funding-sources/v2/persons/'
        async for response in self._requests.fast().fetch(
                url=url + self.phone_number + '/accounts',
                headers=headers,
                method='GET',
                get_json=True
        ):
            return Sum.parse_raw(
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
        if rows_num > 50:
            raise InvalidData('Можно проверять не более 50 транзакций')

        headers = self._auth_token(deepcopy(
            DEFAULT_QIWI_HEADERS
        ))

        payload_data = api_helper.check_dates(
            start_date=start_date,
            end_date=end_date,
            payload_data={
                'rows': rows_num,
                'operation': operation
            }
        )

        base_url = BASE_QIWI_URL + '/payment-history/v2/persons/'
        async for response in self._requests.fast().fetch(
                url=base_url + self.stripped_number + '/payments',
                params=payload_data,
                headers=headers,
                method='GET',
                get_json=True
        ):
            return api_helper.multiply_objects_parse(
                lst_of_objects=(response.response_data.get('data'),),
                model=Transaction
            )

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
            data=deepcopy(QIWI_TO_WALLET),
            to_number=to_number,
            trans_sum=trans_sum,
            currency=currency,
            comment=comment
        )
        data.headers = self._auth_token(
            headers=data.headers
        )
        async for response in self._requests.fast().fetch(
                url=BASE_QIWI_URL + '/sinap/api/v2/terms/99/payments',
                json=data.json,
                headers=data.headers
        ):
            return response.response_data['transaction']['id']

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
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        payload_data = {
            'type': transaction_type
        }
        basic_url = BASE_QIWI_URL + '/payment-history/v1/transactions/'
        async for response in self._requests.fast().fetch(
                url=basic_url + str(transaction_id),
                headers=headers,
                params=payload_data,
                method='GET',
                get_json=True
        ):
            return Transaction.parse_raw(response.response_data)

    async def check_restriction(self) -> Union[
        List[Dict[str, str]], Exception
    ]:
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
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        url = BASE_QIWI_URL + '/person-profile/v1/persons/'
        async for response in self._requests.fast().fetch(
                url=url + self.phone_number + '/status/restrictions',
                headers=headers,
                method='GET'
        ):
            return response.response_data

    async def get_identification(self) -> Identification:
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

        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        url = BASE_QIWI_URL + '/identification/v1/persons/'
        async for response in self._requests.fast().fetch(
                url=url + self.phone_number + '/identification',
                method='GET',
                headers=headers
        ):
            return Identification.parse_raw(response.response_data)

    async def check_transaction(
            self,
            amount: Union[int, float],
            transaction_type: str = 'IN',
            sender: Optional[str] = None,
            rows_num: int = 50,
            comment: Optional[str] = None
    ) -> bool:
        """
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

        elif rows_num > 50:
            raise InvalidData('Можно проверять не более 50 транзакций')

        transactions = await self.transactions(rows_num=rows_num)
        for txn in transactions:
            if float(txn.sum.amount) >= amount:
                if txn.type == transaction_type:
                    if txn.comment == comment and txn.to_account == sender:
                        return True
                    elif comment and sender:
                        continue
                    elif txn.to_account == sender:
                        return True
                    elif sender:
                        continue
                    elif txn.comment == comment:
                        return True
        return False

    async def get_limits(self) -> Dict[str, Limit]:
        """
        Функция для получения лимитов по счёту киви кошелька\n
        Возвращает лимиты по кошельку в виде списка,
        если лимита по определенной стране нет, то не включает его в список
        Подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#limits

        :return: Limit object of Limit(pydantic)
        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))

        payload = {}

        for index, limit_type in enumerate(LIMIT_TYPES):
            payload['types[' + str(index) + ']'] = limit_type
        url = BASE_QIWI_URL + '/qw-limits/v1/persons/'
        async for response in self._requests.fast().fetch(
                url=url + self.stripped_number + '/actual-limits',
                get_json=True,
                headers=headers,
                params=payload,
                method='GET'
        ):
            limits = {}
            for code, limit in response.response_data.get("limits").items():
                if not limit:
                    continue
                limits.update({code: Limit.parse_raw(limit[0])})
            return limits

    async def get_list_of_cards(self) -> dict:
        """
        Данный метод позволяет вам получить список ваших карт.
        Пока ещё в разработке, стабильность сомнительна

        """
        headers = self._auth_token(
            deepcopy(DEFAULT_QIWI_HEADERS)
        )
        async for response in self._requests.fast().fetch(
                url=BASE_QIWI_URL + '/cards/v1/cards?vas-alias=qvc-master',
                method='GET',
                headers=headers
        ):
            return response.response_data

    async def authenticate(
            self,
            birth_date: str,
            first_name: str,
            last_name: str,
            patronymic: str,
            passport: str,
            oms: str = "",
            inn: str = "",
            snils: str = ""
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
            deepcopy(DEFAULT_QIWI_HEADERS)
        )
        url = BASE_QIWI_URL + '/identification/v1/persons/'
        async for response in self._requests.fast().fetch(
                url=url + self.stripped_number + "/identification",
                data=self._requests.filter_dict(payload),
                headers=headers
        ):
            if response.ok and response.status_code == 200:
                return {'success': True}

    async def get_bills(self, rows: int) -> List[Bill]:
        """
        Метод получения списка неоплаченных счетов вашего кошелька.
        Список строится в обратном хронологическом порядке.
        По умолчанию, список разбивается на страницы по 50 элементов в каждой,
        но вы можете задать другое количество элементов (не более 50).
        В запросе можно использовать фильтры по времени выставления счета,
        начальному идентификатору счета.
        """
        headers = self._auth_token(
            deepcopy(DEFAULT_QIWI_HEADERS)
        )
        if rows > 50:
            raise InvalidData('Можно получить не более 50 счетов')
        params = {
            'rows': rows,
            'statuses': 'READY_FOR_PAY'
        }
        async for response in self._requests.fast().fetch(
                url=BASE_QIWI_URL + '/checkout-api/api/bill/search',
                headers=headers,
                method='GET',
                params=params
        ):
            return api_helper.simple_multiply_parse(
                response.response_data.get("bills"), Bill
            )

    async def create_p2p_bill(
            self,
            amount: int,
            bill_id: Optional[str] = None,
            comment: Optional[str] = None,
            life_time: Optional[datetime] = None,
            theme_code: Optional[str] = None,
            pay_source_filter: Optional[str] = None
    ) -> Union[Bill, BillError]:
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
        if not self.secret_p2p:
            raise InvalidData('Не задан p2p токен')

        if not isinstance(bill_id, (str, int)):
            bill_id = str(uuid.uuid4())

        life_time = api_helper.datetime_to_str_in_iso(
            DEFAULT_BILL_TIME if not life_time else life_time
        )

        data = deepcopy(P2P_DATA)

        headers = self._auth_token(data.headers, p2p=True)

        payload = api_helper.set_data_p2p_create(
            wrapped_data=data,
            amount=amount,
            comment=comment,
            theme_code=theme_code,
            pay_source_filter=pay_source_filter,
            life_time=life_time
        )

        async for response in self._requests.fast().fetch(
                url=f'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}',
                json=payload,
                headers=headers,
                method='PUT'
        ):
            return Bill.parse_raw(response.response_data).initialize(self)

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

        data = deepcopy(P2P_DATA)
        headers = self._auth_token(data.headers, p2p=True)
        async for response in self._requests.fast().fetch(
                url=f'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}',
                method='GET',
                headers=headers
        ):
            return Bill.parse_raw(response.response_data).status.value

    async def reject_p2p_bill(self, bill_id: str) -> Bill:
        """
        Метод для отмены транзакции.

        :param bill_id: номер p2p транзакции
        :return: Bill obj
        """
        if not self.secret_p2p:
            raise InvalidData('Не задан p2p токен')
        data = deepcopy(P2P_DATA)
        headers = self._auth_token(data.headers, p2p=True)
        url = f'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}/reject'
        async for response in self._requests.fast().fetch(
                url=url,
                method='POST',
                headers=headers
        ):
            return Bill.parse_raw(response.response_data)

    async def get_receipt(
            self,
            transaction_id: Union[str, int],
            transaction_type: str,
            file_path: Optional[str] = None
    ) -> Union[bytearray, int]:
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
        :param file_path: путь к файлу, куда вы хотите сохранить чек,
         если не указан, возвращает байты
        :return: pdf файл в байтовом виде или номер записанных байтов
        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))

        data = {
            'type': transaction_type,
            'format': 'PDF'
        }

        async for response in self._requests.fast().fetch(
                url=BASE_QIWI_URL + '/payment-history/v1/transactions/' + str(
                    transaction_id) + '/cheque/file',
                headers=headers,
                method='GET',
                params=data
        ):
            if not file_path:
                return response.response_data

            async with aiofiles.open(file_path + '.pdf', 'wb') as file:
                return await file.write(response.response_data)

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
            default_data=COMMISSION_DATA,
            auth_maker=self._auth_token,
            to_account=to_account,
            pay_sum=pay_sum
        )
        if not isinstance(special_code, str):
            special_code = await self._detect_card_number(
                card_number=to_account
            )
        query_url = BASE_QIWI_URL + '/sinap/providers/'
        async for response in self._requests.fast().fetch(
                url=query_url + special_code + '/onlineCommission',
                headers=payload.headers,
                json=payload.json
        ):
            return Commission.parse_raw(response.response_data)

    async def account_info(self) -> QiwiAccountInfo:
        """
        Метод для получения информации об аккаунте

        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        async for response in self._requests.fast().fetch(
                url=BASE_QIWI_URL + '/person-profile/v1/profile/current',
                headers=headers,
                method='GET',
                get_json=True
        ):
            return QiwiAccountInfo.parse_raw(response.response_data)

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
            deepcopy(DEFAULT_QIWI_HEADERS)
        )

        if isinstance(
                start_date, (datetime, timedelta)
        ) and isinstance(
            end_date, (datetime, timedelta)
        ):
            delta = end_date - start_date
            if delta.days > 90:
                raise InvalidData(
                    'Максимальный период для выгрузки'
                    ' статистики - 90 календарных дней.'
                )
        else:
            raise InvalidData(
                'Вы передали значения начальной '
                'и конечной даты в неправильном формате.'
            )

        params = {
            'startDate': api_helper.datetime_to_str_in_iso(start_date),
            'endDate': api_helper.datetime_to_str_in_iso(end_date),
            'operation': operation,
        }

        if sources:
            params.update({'sources': ' '.join(sources)})
        url = BASE_QIWI_URL + '/payment-history/v2/persons/'
        async for response in self._requests.fast().fetch(
                url=url + self.stripped_number + '/payments/total',
                params=params,
                headers=headers,
                get_json=True,
                method='GET'
        ):
            return Statistic.parse_raw(response.response_data)

    async def list_of_balances(self) -> List[Account]:
        """
        Запрос выгружает текущие балансы счетов вашего QIWI Кошелька.
        Более подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#balances_list

        """
        url = BASE_QIWI_URL + '/funding-sources/v2/persons/'
        async for response in self._requests.fast().fetch(
                url=url + self.stripped_number + '/accounts',
                headers=self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS)),
                method='GET'
        ):
            return api_helper.simple_multiply_parse(
                response.response_data.get('accounts'), Account)

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
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        payload = {
            'alias': currency_alias
        }
        url = BASE_QIWI_URL + '/funding-sources/v2/persons/'
        async for response in self._requests.fast().fetch(
                url=url + self.stripped_number + '/accounts',
                headers=headers,
                data=payload
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
        url = BASE_QIWI_URL + '/funding-sources/v2/persons/'
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        async for response in self._requests.fast().fetch(
                url=url + self.stripped_number + '/accounts/offer',
                headers=headers,
                method='GET'
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
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        url = BASE_QIWI_URL + '/funding-sources/v2/persons/'
        async for response in self._requests.fast().fetch(
                url=url + self.stripped_number + '/accounts/' + currency_alias,
                headers=headers,
                method='PATCH',
                json={'defaultAccount': True}
        ):
            return response

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
        url = 'https://api.qiwi.com/partner/bill/v1/bills/' + str(bill_id)
        headers = self._auth_token(
            deepcopy(DEFAULT_QIWI_HEADERS), True
        )
        async for response in self._requests.fast().fetch(
                url=url + ' /refunds/' + refund_id,
                headers=headers,
                method='PUT',
                json=json_bill_data if isinstance(
                    json_bill_data,
                    dict
                ) else json_bill_data.json()
        ):
            return RefundBill.parse_raw(response.response_data)

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
        url, payload = api_helper.qiwi_master_data(self.stripped_number)
        async for response in self._requests.fast().fetch(
                url=url,
                json=payload,
                method='POST',
                headers=self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        ):
            return PaymentInfo.parse_raw(response.response_data)

    async def __pre_qiwi_master_request(
            self,
            card_alias: str = 'qvc-cpa'
    ) -> OrderDetails:
        """
        Метод для выпуска виртуальной карты QIWI Мастер

        :param card_alias: Тип карты
        :return: OrderDetails
        """
        url = BASE_QIWI_URL + "/cards/v2/persons/{number}/orders"
        async for response in self._requests.fast().fetch(
                url=url.format(number=self.stripped_number),
                headers=self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS)),
                json={"cardAlias": card_alias},
                method='POST'
        ):
            return OrderDetails.parse_raw(response.response_data)

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
        url = BASE_QIWI_URL + '/cards/v2/persons/{}/orders'
        async for response in self._requests.fast().fetch(
                url=url.format(
                    self.stripped_number
                ) + f'/{details.order_id}/submit',
                headers=self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS)),
                method='PUT'
        ):
            return OrderDetails.parse_raw(response.response_data)

    async def __buy_new_qiwi_card(
            self,
            **kwargs
    ) -> OrderDetails:
        """
        Покупка карты, если она платная

        :param kwargs:
        :return: OrderDetails
        """
        url, payload = api_helper.new_card_data(**kwargs)
        async for response in self._requests.fast().fetch(
                url=url,
                json=payload,
                headers=self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        ):
            return OrderDetails.parse_raw(response.response_data)

    async def issue_qiwi_master_card(
            self,
            card_alias: str = 'qvc-cpa'
    ) -> OrderDetails:
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
        url = BASE_QIWI_URL + '/cards/v1/cards/?vas-alias=qvc-master'
        async for response in self._requests.fast().fetch(
                url=url,
                headers=self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS)),
                method='GET'
        ):
            return response

    # -*-*-*-*-*-*-*-* WEBHOOKS API -*-*-*-*-*-*-*-*-*-*-*-*-

    async def _register_webhook(
            self,
            web_url: str,
            txn_type: int = 2
    ) -> WebHookConfig:
        """
        This method register a new webhook

        :param web_url: service url
        :param txn_type:  0 => incoming, 1 => outgoing, 2 => all
        :return: Active Hooks
        """
        url = BASE_QIWI_URL + '/payment-notifier/v1/hooks'
        async for response in self._requests.fast().fetch(
                url=url,
                method='PUT',
                headers=self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS)),
                params={
                    'hookType': 1,
                    'param': web_url,
                    'txnType': txn_type
                }
        ):
            return WebHookConfig.parse_raw(response.response_data)

    async def get_current_webhook(self) -> Optional[WebHookConfig]:
        """
        Список действующих (активных) обработчиков уведомлений,
         связанных с вашим кошельком, можно получить данным запросом.
        Так как сейчас используется только один тип хука - webhook,
         то в ответе содержится только один объект данных

        """
        url = BASE_QIWI_URL + '/payment-notifier/v1/hooks/active'
        async for response in self._requests.fast().fetch(
                url=url,
                method='GET',
                headers=self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        ):
            try:
                return WebHookConfig.parse_raw(response.response_data)
            except RequestError:
                return None

    async def _send_test_notification(self) -> Dict[str, str]:
        """
        Для проверки вашего обработчика webhooks используйте данный запрос.
        Тестовое уведомление отправляется на адрес, указанный при вызове
        register_webhook

        """
        url = BASE_QIWI_URL + '/payment-notifier/v1/hooks/test'
        async for response in self._requests.fast().fetch(
                url=url,
                method='GET',
                headers=self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
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
        url = BASE_QIWI_URL + f'/payment-notifier/v1/hooks/{hook_id}/key'
        async for response in self._requests.fast().fetch(
                url=url,
                method='GET',
                headers=self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
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

        url = BASE_QIWI_URL + f'/payment-notifier/v1/hooks/{hook.hook_id}'
        async for response in self._requests.fast().fetch(
                url=url,
                headers=self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS)),
                method='DELETE'
        ):
            return response.response_data

    async def change_webhook_secret(self, hook_id: str) -> str:
        """
        Для смены ключа шифрования уведомлений используйте данный запрос.

        :param hook_id: UUID of webhook
        :return: Base64-закодированный ключ
        """
        url = BASE_QIWI_URL + f'/payment-notifier/v1/hooks/{hook_id}/newkey'
        async for response in self._requests.fast().fetch(
                url=url,
                headers=self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS)),
                method='POST'
        ):
            return response.response_data.get('key')

    async def bind_webhook(
            self,
            url: Optional[str] = None,
            transactions_type: int = 2,
            *,
            send_test_notification: bool = False,
            delete_old: bool = False
    ) -> Tuple[WebHookConfig, str]:
        """
        NON-API EXCLUSIVE method to register new webhook or get old

        :param url: service url
        :param transactions_type: 0 => incoming, 1 => outgoing, 2 => all
        :param send_test_notification:  qiwi will send you test webhook update
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
                )
            key = await self.get_webhook_secret_key(webhook.hook_id)
            return webhook, key

        if send_test_notification:
            await self._send_test_notification()

        if not isinstance(key, str):
            key = await self.get_webhook_secret_key(webhook.hook_id)

        return webhook, key

    def start_webhook(
            self,
            host: str = "localhost",
            port: int = 8080,
            path: Optional[Path] = None,
            app: Optional["web.Application"] = None,
            access_logger: Optional[AbstractAccessLogger] = None,
            **logger_config: Any
    ):
        """
        Blocking function, which listening webhooks

        :param host: server host
        :param port: server port that open for tcp/ip trans.
        :param path: path for qiwi that will send requests
        :param app: pass web.Application
        :param access_logger: pass heir of AbstractAccessLogger,
         if you want custom logger
        """

        app = app if app is not None else web.Application()
        self._requests.without_context = True

        hook_config, key = api_helper.sync(self.bind_webhook)

        server.setup(
            self.handler_manager, app, Path() if not path else path,
            secret_key=self.secret_p2p, base64_key=key
        )

        logging.basicConfig(**logger_config)

        if not isinstance(access_logger, AbstractAccessLogger):
            access_logger = AccessLogger

        web.run_app(
            app,
            host=host,
            port=port,
            access_log_class=access_logger
        )

    @property
    def transaction_handler(self):
        """
        Handler manager for default qiwi transactions,
        you can pass on lambda filter, if you want
        But it must to return bool

        """
        return self.handler_manager.add_transaction_handler

    @property
    def bill_handler(self):
        """
        Handler manager for p2p bills,
        you can pass on lambda filter, if you want
        But it must to return bool
        """
        return self.handler_manager.add_bill_handler
