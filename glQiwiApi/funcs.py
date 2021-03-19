import asyncio
from copy import deepcopy
from datetime import datetime
from typing import Union, Optional, Dict, Literal, List, Type, Iterable
from glQiwiApi.api import HttpXParser
from glQiwiApi.configs import *
from glQiwiApi.data import Response, InvalidCardNumber, WrapperData, Transaction, Identification


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
    def format_objects(iterable_obj: Iterable, obj: Type, transfers: Dict[str, str]) -> Optional[
        List[Union[Transaction, Identification]]]:
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
        Метод для отправки средств на карту, по умолчанию отправляет на киви карту, однако, если вы хотите перевести
        на карту другого типа, вы должны указать prv_id

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
        """Метод для получения индентификатора карты
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
        headers = deepcopy(DEFAULT_QIWI_HEADERS)
        headers = self._auth_token(headers=headers)
        async for response in self._parser.fast().fetch(
                url='https://edge.qiwi.com/funding-sources/v2/persons/' + self.phone_number + '/accounts',
                headers=headers,
                method='GET',
                get_json=True
        ):
            return dict(response.response_data['accounts'][0]['balance'])

    async def transactions(
            self,
            rows_num: int,
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
        headers = deepcopy(DEFAULT_QIWI_HEADERS)
        headers = self._auth_token(
            headers=headers
        )
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
        """https://pypi.org/project/glparser2/0.0.4/
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
            -> Union[dict, str, bytes, bytearray, Exception, None]:
        """
        Метод для получения полной информации о транзакции
        Подробная документация: https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#txn_info

        :param transaction_id: номер транзакции
        :param transaction_type: тип транзакции, может быть только IN или OUT
        :return
        """
        headers = deepcopy(DEFAULT_QIWI_HEADERS)
        headers = self._auth_token(
            headers=headers
        )
        payload_data = {
            'type': transaction_type
        }
        async for response in self._parser.fast().fetch(
                url='https://edge.qiwi.com/payment-history/v1/transactions/' + str(transaction_id),
                headers=headers,
                data=payload_data,
                method='GET'
        ):
            return response.response_data

    async def check_restriction(self) -> Union[List[Dict[str, str]], Exception]:
        """
        Метод для проверки ограничений на вашем киви кошельке\n
        Подробная документация: https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#restrictions

        :return: Список, где находиться словарь с ограничениями, если ограничений нет - возвращает пустой список
        """
        headers = deepcopy(DEFAULT_QIWI_HEADERS)
        headers = self._auth_token(headers=headers)
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
        headers = deepcopy(DEFAULT_QIWI_HEADERS)
        headers = self._auth_token(headers=headers)
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
            sender_number: Optional[str] = None,
            rows_num: int = 50,
            comment: Optional[str] = None) -> bool:
        """
        Метод для проверки транзакции.\n Рекомендуется использовать только если вы не можете написать свой обработчик.\n
        Данный метод использует self.transactions(rows_num=rows_num) для получения платежей.\n
        Для небольшой оптимизации вы можете уменьшить rows_num задав его, однако это не гарантирует правильный результат

        :param amount: сумма платежа
        :param sender_number: номер получателя
        :param rows_num: кол-во платежей, которое будет проверяться
        :param comment: комментарий, по которому будет проверяться транзакция
        :return: bool, есть ли такая транзакция в истории платежей
        """
        transactions = await self.transactions(rows_num=rows_num)
        for transaction in transactions:
            if float(transaction.sum.get('amount')) >= amount and transaction.type == 'IN':
                if transaction.comment == comment and transaction.to_account == sender_number:
                    return True
                elif transaction.to_account == sender_number:
                    return True
        return False
