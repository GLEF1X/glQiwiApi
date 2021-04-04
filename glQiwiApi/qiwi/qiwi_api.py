import functools
import uuid
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Union, Optional, Dict, Literal, List

import aiofiles

from glQiwiApi.abstracts import AbstractPaymentWrapper
from glQiwiApi.aiohttp_custom_api import CustomParser
from glQiwiApi.data import Response, Identification
from glQiwiApi.exceptions import InvalidData, InvalidCardNumber
from glQiwiApi.data_models import QiwiAccountInfo, Transaction, Bill, BillError, Statistic, Limit, Account
from glQiwiApi.data_models.basics import Sum, Commission
from glQiwiApi.qiwi.basic_qiwi_config import *
from glQiwiApi.utils import datetime_to_str_in_iso, DataFormatter, multiply_objects_parse, simple_multiply_parse


class QiwiWrapper(AbstractPaymentWrapper):
    """
    Класс, реализующий обработку запросов к киви, используя основной класс HttpXParser,
    удобен он тем, что не просто отдает json подобные объекты, а всё это конвертирует в python датаклассы.
    Вы также можете импортировать и пользоваться данным классом для парсинга и собственных целей,
    по сути, это обвертка, и вы можете написать такие запросы для любой платежной системы или сайта
    """

    def __init__(self,
                 api_access_token: Optional[str] = None,
                 phone_number: Optional[str] = None,
                 secret_p2p: Optional[str] = None,
                 public_p2p: Optional[str] = None,
                 without_context: bool = False) -> None:
        """
        :param api_access_token: токен, полученный с https://qiwi.com/api
        :param phone_number: номер вашего телефона с +
        :param secret_p2p: секретный ключ, полученный с https://p2p.qiwi.com/
        :param public_p2p: публичный ключ, полученный с https://p2p.qiwi.com/
        :param without_context: булевая переменная, указывающая будет ли объект класса "глобальной" переменной
         или будет использована в async with контексте
        """
        self._parser = CustomParser(without_context=without_context, messages=ERROR_CODE_NUMBERS)
        self.api_access_token = api_access_token
        self.phone_number = phone_number
        self._formatter = DataFormatter()
        self.public_p2p = public_p2p
        self.secret_p2p = secret_p2p

    async def __aenter__(self) -> 'QiwiWrapper':
        """Создаем сессию, чтобы не пересоздавать её много раз"""
        self._parser.create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрываем сессию при выходе"""
        await self._parser.session.close()

    def _auth_token(self, headers: dict, p2p: bool = False) -> dict:
        headers['Authorization'] = headers['Authorization'].format(
            token=self.api_access_token if not p2p else self.secret_p2p
        )
        return headers

    async def to_card(
            self,
            trans_sum: Union[float, int],
            to_card: str
    ) -> Union[Response, str]:
        """
        Метод для отправки средств на карту.
        Более подробная документация https://developer.qiwi.com/ru/qiwi-wallet-personal/#cards

        :param trans_sum: сумма перевода
        :param to_card: номер карты получателя
        :return
        """
        data = deepcopy(QIWI_TO_CARD)
        data.json['sum']['amount'] = trans_sum
        data.json['fields']['account'] = to_card
        data.headers = self._auth_token(headers=data.headers)
        privat_card_id = await self._detect_card_number(card_number=to_card)
        async for response in self._parser.fast().fetch(
                url=BASE_QIWI_URL + '/sinap/api/v2/terms/' + privat_card_id + '/payments',
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
        Метод для получения индентификатора карты

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
                raise InvalidCardNumber('Invalid card number or qiwi_models api is not response') from None

    async def _detect_mobile_number(self, phone_number: str):
        """
        Метод для получения индентификатора телефона

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
            try:
                return response.response_data.get('message')
            except KeyError:
                raise InvalidCardNumber('Invalid card number or qiwi_models api is not response') from None

    async def get_balance(self) -> Sum:
        """Метод для получения баланса киви"""
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        async for response in self._parser.fast().fetch(
                url=BASE_QIWI_URL + '/funding-sources/v2/persons/' + self.phone_number + '/accounts',
                headers=headers,
                method='GET',
                get_json=True
        ):
            return Sum.parse_raw(response.response_data['accounts'][0]['balance'])

    async def transactions(
            self,
            rows_num: int = 50,
            operation: Literal['ALL', 'IN', 'OUT', 'QIWI_CARD', 'ALL'] = 'ALL',
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> Union[Optional[List[Transaction]], dict]:
        """
        Метод для получения транзакций на счёту
        Более подробная документация https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#payments_list

        :param rows_num: кол-во транзакций, которые вы хотите получить
        :param operation: Тип операций в отчете, для отбора.
        :param start_date:Начальная дата поиска платежей. Используется только вместе с end_date.
        :param end_date: онечная дата поиска платежей. Используется только вместе со start_date.

        """
        if rows_num > 50:
            raise InvalidData('Можно проверять не более 50 транзакций')

        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        payload_data = {
            'rows': rows_num,
            'operation': operation
        }

        if isinstance(start_date, (datetime, timedelta)) and isinstance(end_date, (datetime, timedelta)):
            if (end_date - start_date).total_seconds() > 0:
                payload_data.update(
                    {
                        'startDate': datetime_to_str_in_iso(start_date),
                        'endDate': datetime_to_str_in_iso(end_date)
                    }
                )
            else:
                raise InvalidData('end_date не может быть больше чем start_date')
        async for response in self._parser.fast().fetch(
                url=BASE_QIWI_URL + '/payment-history/v2/persons/' + self.phone_number.replace('+', '') + '/payments',
                params=payload_data,
                headers=headers,
                method='GET',
                get_json=True
        ):
            return multiply_objects_parse(
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
        Подробная документация: https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#p2p

        :param to_number: номер получателя
        :param trans_sum: кол-во денег, которое вы хотите перевести
        :param currency: особенный код валюты
        :param comment: комментарий к платёжу
        """
        data = self._formatter.set_data_to_wallet(
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
            transaction_type: Literal['IN', 'OUT']) \
            -> Optional[Transaction]:
        """
        Метод для получения полной информации о транзакции\n
        Подробная документация: https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#txn_info

        :param transaction_id: номер транзакции
        :param transaction_type: тип транзакции, может быть только IN или OUT
        :return: Transaction object
        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        payload_data = {
            'type': transaction_type
        }
        async for response in self._parser.fast().fetch(
                url=BASE_QIWI_URL + '/payment-history/v1/transactions/' + str(transaction_id),
                headers=headers,
                params=payload_data,
                method='GET',
                get_json=True
        ):
            return Transaction.parse_raw(response.response_data)

    async def check_restriction(self) -> Union[List[Dict[str, str]], Exception]:
        """
        Метод для проверки ограничений на вашем киви кошельке\n
        Подробная документация: https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#restrictions

        :return: Список, где находиться словарь с ограничениями, если ограничений нет - возвращает пустой список
        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        async for response in self._parser.fast().fetch(
                url=BASE_QIWI_URL + '/person-profile/v1/persons/' + self.phone_number + '/status/restrictions',
                headers=headers,
                method='GET'
        ):
            return response.response_data

    async def get_identification(self) -> List[Identification]:
        """
        Функция, которая позволяет получить данные индентификации вашего киви кошелька
        Более подробная документация https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#ident

        :return: Response object
        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        async for response in self._parser.fast().fetch(
                url=BASE_QIWI_URL + '/identification/v1/persons/' + self.phone_number + '/identification',
                method='GET',
                headers=headers
        ):
            return self._formatter.format_objects(
                iterable_obj=(response.response_data,),
                obj=Identification,
                transfers=IDENTIFICATION_TRANSFER
            )

    async def check_transaction(
            self,
            amount: Union[int, float],
            transaction_type: Literal['IN', 'OUT', 'QIWI_CARD'] = 'IN',
            sender_number: Optional[str] = None,
            rows_num: int = 50,
            comment: Optional[str] = None) -> bool:
        """
        Метод для проверки транзакции.\n Рекомендуется использовать только если вы не можете написать свой обработчик.\n
        Данный метод использует self.transactions(rows_num=rows_num) для получения платежей.\n
        Для небольшой оптимизации вы можете уменьшить rows_num задав его, однако это не гарантирует правильный результат

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
            if float(transaction.sum.amount) >= amount and transaction.type == transaction_type:
                if transaction.comment == comment and transaction.to_account == sender_number:
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
        Возвращает лимиты по кошельку в виде списка, если лимита по определенной стране нет, то не включает его в список
        Подробная документация https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#limits

        :return: Limit object of Limit(pydantic)
        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))

        payload = {}

        for index, limit_type in enumerate(LIMIT_TYPES):
            payload['types[' + str(index) + ']'] = limit_type

        async for response in self._parser.fast().fetch(
                url=BASE_QIWI_URL + '/qw-limits/v1/persons/' + self.phone_number.replace("+", "") + '/actual-limits',
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
        Данный метод позволяет вам получить список ваших карт. Пока ещё в разработке, стабильность сомнительна

        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
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
        Данный запрос позволяет отправить данные для идентификации вашего QIWI кошелька.
        Допускается идентифицировать не более 5 кошельков на одного владельца

        Для идентификации кошелька вы обязательно должны отправить ФИО, серию/номер паспорта и дату рождения.\n
        Если данные прошли проверку, то в ответе будет отображен
        ваш ИНН и упрощенная идентификация кошелька будет установлена.
        В случае если данные не прошли проверку, кошелек остается в статусе "Минимальный".
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
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        async for response in self._parser.fast().fetch(
                url=BASE_QIWI_URL + '/identification/v1/persons/' + self.phone_number.replace("+",
                                                                                              "") + "/identification",
                data=payload,
                headers=headers
        ):
            if response.ok and response.status_code == 200:
                return {'success': True}

    async def get_bills(self, rows: int) -> List[Bill]:
        """
        Метод получения списка неоплаченных счетов вашего кошелька.
        Список строится в обратном хронологическом порядке.
        По умолчанию, список разбивается на страницы по 50 элементов в каждой, но вы можете задать другое количество
        элементов (не более 50). В запросе можно использовать фильтры по времени выставления счета,
        начальному идентификатору счета.
        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        if rows > 50:
            raise InvalidData('Можно получить не более 50 счетов')
        params = {
            'rows': rows
        }
        async for response in self._parser.fast().fetch(
                url=BASE_QIWI_URL + '/checkout-api/api/bill/search?statuses=READY_FOR_PAY',
                headers=headers,
                method='GET',
                params=params
        ):
            return simple_multiply_parse(response.response_data.get("bills"), Bill)

    async def create_p2p_bill(
            self,
            amount: int,
            bill_id: Optional[str] = None,
            comment: Optional[str] = None,
            life_time: Optional[datetime] = None,
            theme_code: Optional[str] = None,
            pay_source_filter: Optional[Literal['qw', 'card', 'mobile']] = None
    ) -> Union[Bill, BillError]:
        """
        Метод для выставление p2p счёта.
        Надежный способ для интеграции. Параметры передаются server2server с использованием авторизации.


        :param amount: сумма платежа
        :param bill_id: уникальный номер транзакции, если не передан, генерируется автоматически,
        :param life_time: дата, до которой счет будет доступен для оплаты.
        :param comment: комментарий к платёжу
        :param theme_code: специальный код темы
        :param pay_source_filter: При открытии формы будут отображаться только указанные способы перевода
        """
        if not self.public_p2p or not self.secret_p2p:
            raise InvalidData('Не задан p2p токен')

        if not bill_id:
            bill_id = str(uuid.uuid4())

        life_time = datetime_to_str_in_iso((datetime.now() + timedelta(days=2)) if not life_time else life_time)
        data = deepcopy(P2P_DATA)
        headers = self._auth_token(data.headers, p2p=True)
        payload = self._formatter.set_data_p2p_create(
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
            # unparsed_data = str(json.dumps(response.response_data))
            return Bill.parse_raw(response.response_data).initialize(self)

    async def check_p2p_bill_status(self, bill_id: str) -> Literal['WAITING', 'PAID', 'REJECTED', 'EXPIRED']:
        """
        Метод для проверки статуса p2p транзакции.\n
        Возможные типы транзакции: \n
        WAITING	Счет выставлен, ожидает оплаты	\n
        PAID	Счет оплачен	\n
        REJECTED	Счет отклонен\n
        EXPIRED	Время жизни счета истекло. Счет не оплачен\n
        Более подробная документация https://developer.qiwi.com/ru/p2p-payments/?shell#invoice-status

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
        :return: транзакцию в датаклассе
        """
        if not self.public_p2p or not self.secret_p2p:
            raise InvalidData('Не задан p2p токен')
        data = deepcopy(P2P_DATA)
        headers = self._auth_token(data.headers, p2p=True)
        async for response in self._parser.fast().fetch(
                url=f'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}/reject',
                method='POST',
                headers=headers
        ):
            return Bill.parse_raw(response.response_data)

    @functools.lru_cache
    async def get_receipt(
            self,
            transaction_id: Union[str, int],
            transaction_type: Literal['IN', 'OUT', 'QIWI_CARD'],
            file_path: Optional[str] = None
    ) -> Union[bytearray, int]:
        """
        Метод для получения чека в формате байтов или файлом.

        :param transaction_id: айди транзакции, можно получить при вызове методе to_wallet, to_card
        :param transaction_type: тип транзакции может быть 'IN', 'OUT', 'QIWI_CARD'
        :param file_path: путь к файлу, куда вы хотите сохранить чек, если не указан, возвращает байты
        :return: pdf файл в байтовом виде или номер записанных байтов
        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        data = {
            'type': transaction_type,
            'format': 'PDF'
        }
        async for response in self._parser.fast().fetch(
                url=BASE_QIWI_URL + '/payment-history/v1/transactions/' + str(transaction_id) + '/cheque/file',
                headers=headers,
                method='GET',
                params=data
        ):
            if not file_path:
                return response.response_data

            async with aiofiles.open(file_path + '.pdf', 'wb') as file:
                return await file.write(response.response_data)

    async def commission(self, to_account: str, pay_sum: Union[int, float]) -> Commission:
        """
        Возвращается полная комиссия QIWI Кошелька за платеж в пользу указанного провайдера
        с учетом всех тарифов по заданному набору платежных реквизитов.

        :param to_account: номер карты или киви кошелька
        :param pay_sum: сумма, за которую вы хотите узнать коммиссию
        :return: Commission object
        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        json_payload = deepcopy(ONLINE_COMMISSION_DATA)
        json_payload['purchaseTotals']['total']['amount'] = pay_sum
        json_payload['account'] = to_account.replace('+', '')
        special_code = "99" if len(to_account.replace('+', '')) <= 15 else (
            await self._detect_card_number(card_number=to_account))
        async for response in self._parser.fast().fetch(
                url=BASE_QIWI_URL + '/sinap/providers/' + special_code + '/onlineCommission',
                headers=headers,
                json=json_payload
        ):
            return Commission.parse_raw(response.response_data)

    async def account_info(self) -> QiwiAccountInfo:
        """Метод для получения информации об аккаунте"""
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        async for response in self._parser.fast().fetch(
                url=BASE_QIWI_URL + '/person-profile/v1/profile/current',
                headers=headers,
                method='GET',
                get_json=True
        ):
            return QiwiAccountInfo.parse_raw(response.response_data)

    async def fetch_statistics(
            self, start_date: Union[datetime, timedelta], end_date: Union[datetime, timedelta],
            operation: Literal['ALL', 'IN', 'OUT', 'QIWI_CARD'] = 'ALL',
            sources: Optional[List[Literal['QW_RUB', 'CARD', 'QW_USD', 'QW_EUR', 'MK']]] = None
    ) -> Statistic:
        """
        Данный запрос используется для получения сводной статистики по суммам платежей за заданный период.\n
        Более подробная документация: https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#payments_list

        :param start_date: Начальная дата периода статистики. Обязательный параметр
        :param end_date: Конечная дата периода статистики. Обязательный параметр
        :param operation: Тип операций, учитываемых при подсчете статистики. Допустимые значения:
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
            MK - счет мобильного оператора. Если не указан, учитываются все источники платежа.
        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))

        if isinstance(start_date, (datetime, timedelta)) and isinstance(end_date, (datetime, timedelta)):
            delta = end_date - start_date
            if delta.days > 90:
                raise InvalidData('Максимальный период для выгрузки статистики - 90 календарных дней.')
        else:
            raise InvalidData('Вы передали значения начальной и конечной даты в неправильном формате.')

        params = {
            'startDate': datetime_to_str_in_iso(start_date),
            'endDate': datetime_to_str_in_iso(end_date),
            'operation': operation,
        }

        if sources:
            params.update({'sources': ' '.join(sources)})
        async for response in self._parser.fast().fetch(
                url=BASE_QIWI_URL + '/payment-history/v2/persons/' + self.phone_number.replace("+",
                                                                                               "") + '/payments/total',
                params=params,
                headers=headers,
                get_json=True,
                method='GET'
        ):
            return Statistic.parse_raw(response.response_data)

    async def list_of_balances(self) -> List[Account]:
        """
        Запрос выгружает текущие балансы счетов вашего QIWI Кошелька.
        Более подробная документация: https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#balances_list
        """

        async for response in self._parser.fast().fetch(
                url=BASE_QIWI_URL + '/funding-sources/v2/persons/' + self.phone_number.replace("+", "") + '/accounts',
                headers=self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS)),
                method='GET'
        ):
            return simple_multiply_parse(response.response_data.get('accounts'), Account)
