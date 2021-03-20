import asyncio
from copy import deepcopy
from datetime import datetime
from typing import Union, Optional, Dict, Literal, List, Type, Iterable
from glQiwiApi.api import HttpXParser
from glQiwiApi.configs import *
from glQiwiApi.configs import LIMIT_TYPES_TRANSFER
from glQiwiApi.data import Response, InvalidCardNumber, WrapperData, Transaction, Identification, InvalidData, Limit


class QiwiDataFormatter:

    @staticmethod
    def set_data_to_wallet(
            data: WrapperData,
            to_number: str,
            trans_sum: Union[str, int, float],
            comment: str,
            currency: str = '643'):
        data.json['sum']['amount'] = str(trans_sum)
        data.json['sum']['currency'] = currency
        data.json['fields']['account'] = to_number
        data.json['comment'] = comment
        data.headers.update({'User-Agent': 'Android v3.2.0 MKT'})
        return data

    @staticmethod
    def format_objects(
            iterable_obj: Iterable,
            obj: Type,
            transfers: Dict[str, str]
    ) -> Optional[List[Union[Transaction, Identification, Limit]]]:
        kwargs = {}
        objects = []
        for transaction in iterable_obj:
            for key, value in transaction.items():
                if key in obj.__dict__.get('__annotations__').keys():
                    kwargs.update({
                        key: value
                    })
                elif key in transfers.keys():
                    kwargs.update({
                        transfers.get(key): value
                    })
            objects.append(obj(**kwargs))
            kwargs = {}
        return objects


class QiwiWrapper:
    """
    Класс, реализующий обработку запросов к киви, используя основной класс HttpXParser,
    удобен он тем, что не просто отдает json подобные объекты, а всё это конвертирует в python датаклассы.
    Вы также можете импортировать и пользоваться данным классом для парсинга и собственных целей,
    по сути, это обвертка, и вы можете написать такие запросы для любой платежной системы или сайта
    """

    def __init__(self, api_access_token: str, phone_number: str) -> None:
        self._parser = HttpXParser()
        self.api_access_token = api_access_token
        self.phone_number = phone_number
        self._formatter = QiwiDataFormatter()

    def _auth_token(self, headers: dict) -> dict:
        headers['Authorization'] = headers['Authorization'].format(
            token=self.api_access_token
        )
        return headers

    async def to_card(
            self,
            trans_sum: Union[float, int],
            to_card: str
    ) -> Response:
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
                url='https://edge.qiwi.com/sinap/api/v2/terms/' + privat_card_id + '/payments',
                headers=data.headers,
                json=data.json,
                get_json=True
        ):
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
                raise InvalidCardNumber('Invalid card number or qiwi api is not response') from None

    async def get_balance(self) -> Dict[str, int]:
        """Метод для получения баланса киви, принимает\n логин(номер телефона) и токен с https://qiwi.com/api"""
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        async for response in self._parser.fast().fetch(
                url='https://edge.qiwi.com/funding-sources/v2/persons/' + self.phone_number + '/accounts',
                headers=headers,
                method='GET',
                get_json=True
        ):
            return dict(response.response_data['accounts'][0]['balance'])

    async def transactions(
            self,
            rows_num: int = 50,
            operation: Literal['ALL', 'IN', 'OUT', 'QIWI_CARD', 'ALL'] = 'ALL',
            start_date: Optional[Union[str, datetime]] = None,
            end_date: Optional[Union[str, datetime]] = None
    ) -> Union[Optional[List[Transaction]], dict]:
        """
        Метод для получения транзакций на счёту
        Более подробная документация https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#payments_list

        :param rows_num: кол-во транзакций, которые вы хотите получить
        :param operation: Тип операций в отчете, для отбора.
        :param start_date:Начальная дата поиска платежей. Используется только вместе с endDate.
        :param end_date: онечная дата поиска платежей. Используется только вместе со startDate.

        """
        if rows_num > 50:
            raise InvalidData('Можно проверять не более 50 транзакций')
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        payload_data = {
            'rows': rows_num,
            'operation': operation
        }
        if isinstance(start_date, (datetime, str)) and isinstance(end_date, (datetime, str)):
            payload_data.update(
                {
                    'startDate': start_date,
                    'endDate': end_date
                }
            )
        async for response in self._parser.fast().fetch(
                url='https://edge.qiwi.com/payment-history/v2/persons/' +
                    self.phone_number.replace('+', '')
                    + '/payments',
                data=payload_data,
                headers=headers,
                method='GET'
        ):
            try:
                return self._formatter.format_objects(
                    iterable_obj=response.response_data.get('data'),
                    obj=Transaction,
                    transfers=TRANSACTION_TRANSFER
                )
            except IndexError:
                return dict()

    async def to_wallet(
            self,
            to_number: str,
            trans_sum: Union[str, float, int],
            currency: str = '643',
            comment: str = '+comment+') -> Response:
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
                url='https://edge.qiwi.com/sinap/api/v2/terms/99/payments',
                json=data.json,
                headers=data.headers
        ):
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
                url='https://edge.qiwi.com/payment-history/v1/transactions/' + str(transaction_id),
                headers=headers,
                data=payload_data,
                method='GET'
        ):
            return self._formatter.format_objects(
                iterable_obj=(response.response_data,),
                obj=Transaction,
                transfers=TRANSACTION_TRANSFER
            )

    async def check_restriction(self) -> Union[List[Dict[str, str]], Exception]:
        """
        Метод для проверки ограничений на вашем киви кошельке\n
        Подробная документация: https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#restrictions

        :return: Список, где находиться словарь с ограничениями, если ограничений нет - возвращает пустой список
        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        async for response in self._parser.fast().fetch(
                url='https://edge.qiwi.com/person-profile/v1/persons/' + self.phone_number + '/status/restrictions',
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
                url='https://edge.qiwi.com/identification/v1/persons/' + self.phone_number + '/identification',
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
            if float(transaction.sum.get('amount')) >= amount and transaction.type == transaction_type:
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

    async def get_limits(self) -> List[Limit]:
        """
        Функция для получения лимитов по счёту киви кошелька\n
        Возвращает лимиты по кошельку в виде списка, если лимита по определенной стране нет, то не включает его в список
        Подробная документация https://developer.qiwi.com/ru/qiwi-wallet-personal/?http#limits

        :return: Limit object of dataclass
        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))

        payload = {}

        for index, limit_type in enumerate(LIMIT_TYPES):
            payload['types[' + str(index) + ']'] = limit_type

        async for response in self._parser.fast().fetch(
                url='https://edge.qiwi.com/qw-limits/v1/persons/'
                    + self.phone_number.replace("+", "")
                    + '/actual-limits',
                get_json=True,
                headers=headers,
                data=payload,
                method='GET'
        ):
            limits = []
            for key, value in response.response_data.get('limits').items():
                limit = self._formatter.format_objects(
                    iterable_obj=value,
                    transfers=LIMIT_TYPES_TRANSFER,
                    obj=Limit
                )
                try:
                    if isinstance(limit[0], Limit):
                        limit[0].limit_country_code = key
                        limits.append(limit[0])
                except IndexError:
                    continue

            return limits

    async def get_list_of_cards(self) -> dict:
        """
        Данный метод позволяет вам получить список ваших карт. Пока ещё в разработке, стабильность сомнительна

        """
        headers = self._auth_token(deepcopy(DEFAULT_QIWI_HEADERS))
        async for response in self._parser.fast().fetch(
                url='https://edge.qiwi.com/cards/v1/cards?vas-alias=qvc-master',
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
        Если данные прошли проверку, то в ответе будет отображен ваш ИНН и упрощенная идентификация кошелька будет установлена.
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
                url='https://edge.qiwi.com/identification/v1/persons/' +
                    self.phone_number.replace("+", "") +
                    "/identification",
                data=payload,
                headers=headers
        ):
            if response.ok and response.status_code == 200:
                return {'success': True}