import uuid
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Union, Optional, Dict, List, Any

import aiofiles

import glQiwiApi.utils.basics as api_helper
from glQiwiApi.abstracts import AbstractPaymentWrapper
from glQiwiApi.aiohttp_custom_api import CustomParser
from glQiwiApi.mixins import ToolsMixin
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
    Response,
    Sum,
    Commission,
    OptionalSum
)
from glQiwiApi.types.basics import DEFAULT_CACHE_TIME
from glQiwiApi.types.qiwi_types.bill import RefundBill
from glQiwiApi.utils.exceptions import InvalidData, InvalidCardNumber

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
        'public_p2p',
        '_parser',
    )

    def __init__(
            self,
            api_access_token: Optional[str] = None,
            phone_number: Optional[str] = None,
            secret_p2p: Optional[str] = None,
            public_p2p: Optional[str] = None,
            without_context: bool = False,
            cache_time: Union[float, int] = DEFAULT_CACHE_TIME
    ) -> None:
        """
        :param api_access_token: токен, полученный с https://qiwi.com/api
        :param phone_number: номер вашего телефона с +
        :param secret_p2p: секретный ключ, полученный с https://p2p.qiwi.com/
        :param public_p2p: публичный ключ, полученный с https://p2p.qiwi.com/
        :param without_context: bool, указывает будет ли объект класса
         "глобальной" переменной или будет использована в async with контексте
        :param cache_time: Время кэширование запросов в секундах,
         по умолчанию 0, соответственно,
         запрос не будет использовать кэш по дефолту, максимальное время
         кэширование 60 секунд
        """
        super().__init__()

        if isinstance(phone_number, str):
            self.phone_number = phone_number.replace('+', '')
            if self.phone_number.startswith('8'):
                self.phone_number = '7' + self.phone_number[1:]
        self._parser = CustomParser(
            without_context=without_context,
            messages=ERROR_CODE_NUMBERS,
            cache_time=cache_time
        )
        self.api_access_token = api_access_token
        self.public_p2p = public_p2p
        self.secret_p2p = secret_p2p

    def _auth_token(self, headers: dict, p2p: bool = False) -> dict:
        headers['Authorization'] = headers['Authorization'].format(
            token=self.api_access_token if not p2p else self.secret_p2p
        )
        return headers

    @property
    def stripped_number(self) -> str:
        return self.phone_number.replace("+", "")

    async def to_card(
            self,
            trans_sum: Union[float, int],
            to_card: str
    ) -> Union[Response, str]:
        """
        Метод для отправки средств на карту.
        Более подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/#cards

        :param trans_sum: сумма перевода
        :param to_card: номер карты получателя
        :return
        """
        data = deepcopy(QIWI_TO_CARD)
        data.json['sum']['amount'] = trans_sum
        data.json['fields']['account'] = to_card
        data.headers = self._auth_token(headers=data.headers)
        privat_card_id = await self._detect_card_number(card_number=to_card)
        base_url = BASE_QIWI_URL + '/sinap/api/v2/terms/' + privat_card_id
        async for response in self._parser.fast().fetch(
                url=base_url + '/payments',
                headers=data.headers,
                json=data.json,
                get_json=True
        ):
            try:
                return response.response_data.get('id')
            except (KeyError, TypeError):
                return response

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
        async for response in self._parser.fetch(
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
        async for response in self._parser.fetch(
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
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        url = BASE_QIWI_URL + '/funding-sources/v2/persons/'
        async for response in self._parser.fast().fetch(
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
    ) -> Union[Optional[List[Transaction]], dict]:
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
        payload_data = {
            'rows': rows_num,
            'operation': operation
        }

        if isinstance(
                start_date, (datetime, timedelta)
        ) and isinstance(
            end_date, (datetime, timedelta)
        ):
            if (end_date - start_date).total_seconds() > 0:
                payload_data.update(
                    {
                        'startDate': api_helper.datetime_to_str_in_iso(
                            start_date
                        ),
                        'endDate': api_helper.datetime_to_str_in_iso(
                            end_date
                        )
                    }
                )
            else:
                raise InvalidData(
                    'end_date не может быть больше чем start_date'
                )
        base_url = BASE_QIWI_URL + '/payment-history/v2/persons/'
        async for response in self._parser.fast().fetch(
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
            comment: str = '+comment+') -> Union[str, Response]:
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
        async for response in self._parser.fast().fetch(
                url=BASE_QIWI_URL + '/sinap/api/v2/terms/99/payments',
                json=data.json,
                headers=data.headers
        ):
            try:
                return response.response_data['transaction']['id']
            except (KeyError, TypeError):
                return response

    async def transaction_info(
            self,
            transaction_id: Union[str, int],
            transaction_type: str
    ) -> Optional[Transaction]:
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
        async for response in self._parser.fast().fetch(
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
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        url = BASE_QIWI_URL + '/person-profile/v1/persons/'
        async for response in self._parser.fast().fetch(
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
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        url = BASE_QIWI_URL + '/identification/v1/persons/'
        async for response in self._parser.fast().fetch(
                url=url + self.phone_number + '/identification',
                method='GET',
                headers=headers
        ):
            return Identification.parse_raw(response.response_data)

    async def check_transaction(
            self,
            amount: Union[int, float],
            transaction_type: str = 'IN',
            sender_number: Optional[str] = None,
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
        :param sender_number: номер получателя
        :param rows_num: кол-во платежей, которое будет проверяться
        :param comment: комментарий, по которому будет проверяться транзакция
        :return: bool, есть ли такая транзакция в истории платежей
        """
        if transaction_type not in ['IN', 'OUT', 'QIWI_CARD']:
            raise InvalidData('Вы ввели неправильный метод транзакции')

        elif rows_num > 50:
            raise InvalidData('Можно проверять не более 50 транзакций')

        transactions = await self.transactions(rows_num=rows_num)
        for transaction in transactions:
            if float(transaction.sum.amount) >= amount:
                if transaction.type == transaction_type:
                    if transaction.comment == comment:
                        if transaction.to_account == sender_number:
                            return True
                    elif comment and sender_number:
                        continue
                    elif transaction.to_account == sender_number:
                        return True
                    elif sender_number:
                        continue
                    elif transaction.comment == comment:
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
        async for response in self._parser.fast().fetch(
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
        async for response in self._parser.fast().fetch(
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
        async for response in self._parser.fast().fetch(
                url=url + self.stripped_number + "/identification",
                data=payload,
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
        async for response in self._parser.fast().fetch(
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
        if not self.public_p2p or not self.secret_p2p:
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

        async for response in self._parser.fast().fetch(
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
        if not self.public_p2p or not self.secret_p2p:
            raise InvalidData('Не задан p2p токен')

        data = deepcopy(P2P_DATA)
        headers = self._auth_token(data.headers, p2p=True)
        async for response in self._parser.fast().fetch(
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
        if not self.public_p2p or not self.secret_p2p:
            raise InvalidData('Не задан p2p токен')
        data = deepcopy(P2P_DATA)
        headers = self._auth_token(data.headers, p2p=True)
        url = f'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}/reject'
        async for response in self._parser.fast().fetch(
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
        async for response in self._parser.fast().fetch(
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
        payload = deepcopy(COMMISSION_DATA)
        headers = self._auth_token(payload.headers)
        payload.json['purchaseTotals']['total']['amount'] = pay_sum
        payload.json['account'] = to_account.replace('+', '')
        special_code = "99" if len(to_account.replace('+', '')) <= 15 else (
            await self._detect_card_number(card_number=to_account))
        query_url = BASE_QIWI_URL + '/sinap/providers/'
        async for response in self._parser.fast().fetch(
                url=query_url + special_code + '/onlineCommission',
                headers=headers,
                json=payload.json
        ):
            return Commission.parse_raw(response.response_data)

    async def account_info(self) -> QiwiAccountInfo:
        """
        Метод для получения информации об аккаунте

        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        async for response in self._parser.fast().fetch(
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
        async for response in self._parser.fast().fetch(
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
        async for response in self._parser.fast().fetch(
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
        async for response in self._parser.fast().fetch(
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
        async for response in self._parser.fast().fetch(
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
        async for response in self._parser.fast().fetch(
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
        async for response in self._parser.fast().fetch(
                url=url + ' /refunds/' + refund_id,
                headers=headers,
                method='PUT',
                json=json_bill_data if isinstance(
                    json_bill_data,
                    dict
                ) else json_bill_data.json()
        ):
            return RefundBill.parse_raw(response.response_data)
