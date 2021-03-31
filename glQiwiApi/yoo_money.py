import asyncio
from datetime import datetime
from typing import List, Dict, Any, Union, Optional, Tuple
from glQiwiApi import HttpXParser

from glQiwiApi.configs import BASE_YOOMONEY_URL, OPERATION_TRANSFER
from glQiwiApi.data import AccountInfo, OperationType, ALL_OPERATION_TYPES, Operation
from glQiwiApi.exceptions import NoUrlFound, InvalidData
from glQiwiApi.utils import parse_auth_link, parse_headers, DataFormatter, measure_time, datetime_to_str_in_iso

TOKEN = '4100116602400968.44E1736C18ED0C1BFF6B1A0B468CDE971A25E0006B242F71591DB8B86C1BDAEB383E5B5BFF64BB82D7EA8060BFCFCE4388D0F2166A1F64E0822DE5C7DC9AFBC2E123A4C7C06F7645F047EBBEEB0C76B56B8BAD708151933C060891C3D6C5585F24029AFD57EBAB8A82C34405CAC9D208E8A1644F2879BA4A136A244A48AB56E9'


class YooMoney(object):

    def __init__(self, api_access_token: str) -> None:
        """
        Конструктор принимает только токен, полученный из класс методов этого же класса

        :param api_access_token: апи токен для запросов
        """
        self.api_access_token = api_access_token
        self.__content_and_auth = {'content_json': True, 'auth': True}
        self._parser = HttpXParser()
        self._formatter = DataFormatter()

    def _auth_token(self, headers: dict) -> Dict[Any, Any]:
        headers['Authorization'] = headers['Authorization'].format(
            token=self.api_access_token
        )
        return headers

    @classmethod
    async def build_url_for_auth(cls, scope: List[str], client_id: str,
                                 redirect_uri: str = 'https://example.com') -> str:
        """
        Метод для получения ссылки для дальнейшей авторизации и получения токена yoomoney\n
        Сценарий авторизации, взятый из документации, приложения пользователем:\n
        1. Пользователь инициирует авторизацию приложения для управления своим счетом.\n
        2. Приложение отправляет запрос Authorization Request на сервер ЮMoney.\n
        3. ЮMoney перенаправляют пользователя на страницу авторизации.\n
        4. Пользователь вводит свой логин и пароль,
           просматривает список запрашиваемых прав и подтверждает, либо отклоняет запрос авторизации.
        5. Приложение получает ответ Authorization Response
         в виде HTTP Redirect со временным токеном для получения доступа или кодом ошибки.\n
        6. Приложение, используя полученный временный токен доступа,
           отправляет запрос на получение токена авторизации (Access Token Request).\n
        7. Ответ содержит токен авторизации (access_token).\n
        8. Приложение сообщает пользователю результат авторизации.\n
        Подробно это описано в оффициальной документации:
        https://yoomoney.ru/docs/wallet/using-api/authorization/request-access-token

        :param scope: OAuth2-авторизации приложения пользователем, права перечисляются через пробел.
        :param client_id: идентификатор приложения, тип string
        :param redirect_uri: воронка, куда прийдет временный код, который нужен для получения основного токена
        :return: ссылку, по которой нужно перейти и сделать авторизацию через логин/пароль
        """
        headers = parse_headers()
        params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': " ".join(scope)
        }
        async for response in HttpXParser().fast().fetch(
                url=BASE_YOOMONEY_URL + '/oauth/authorize',
                headers=headers,
                data=params,
                method='POST'
        ):
            try:
                return parse_auth_link(response.response_data)
            except IndexError:
                raise NoUrlFound('Не удалось найти ссылку для авторизации в ответе от апи, проверятьте client_id')

    @classmethod
    async def get_access_token(cls, code: str, client_id: str, redirect_uri: str = 'https://example.com') -> str:
        """
        Метод для получения токена для запросов к YooMoney API

        :param code: временный код, который был получен в методе base_authorize
        :param client_id: идентификатор приложения, тип string
        :param redirect_uri: воронка, куда прийдет временный код, который нужен для получения основного токена
        :return: YooMoney API TOKEN
        """
        headers = parse_headers(content_json=True)
        params = {
            'code': code,
            'client_id': client_id,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        async for response in HttpXParser().fast().fetch(
                url=BASE_YOOMONEY_URL + '/oauth/token',
                headers=headers,
                data=params,
                method='POST',
                get_json=True
        ):
            return response.response_data.get('access_token')

    async def revoke_api_token(self) -> bool:
        """
        Метод для отзывания токена, при этом все его права тоже пропадают
        Документация: https://yoomoney.ru/docs/wallet/using-api/authorization/revoke-access-token
        """
        headers = self._auth_token(parse_headers(auth=True))
        async for response in self._parser.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/revoke',
                method='POST',
                headers=headers
        ):
            return response.ok

    async def account_info(self) -> AccountInfo:
        """
        Метод для получения информации об аккаунте пользователя
        Подробная документация: https://yoomoney.ru/docs/wallet/user-account/account-info

        :return: объект AccountInfo
        """
        headers = self._auth_token(parse_headers(**self.__content_and_auth))
        async for response in self._parser.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/account-info',
                headers=headers,
                method='POST'
        ):
            try:
                return self._formatter.format_objects(
                    iterable_obj=(response.response_data,),
                    obj=AccountInfo
                )[0]
            except IndexError:
                raise InvalidData('Cannot fetch account info, check your token')

    async def get_operation_history(
            self,
            operation_types: Optional[Union[List[OperationType], Tuple[OperationType]]] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            start_record: Optional[int] = None,
            records: int = 30,
            label: Optional[Union[str, int]] = None
    ):
        """
        Подробная документация: https://yoomoney.ru/docs/wallet/user-account/operation-history\n
        Метод позволяет просматривать историю операций (полностью или частично) в постраничном режиме.\n
        Записи истории выдаются в обратном хронологическом порядке: от последних к более ранним.\n
        Перечень типов операций, которые требуется отобразить. Возможные значения:\n
        DEPOSITION — пополнение счета (приход);\n
        PAYMENT — платежи со счета (расход);\n
        INCOMING(incoming-transfers-unaccepted) — непринятые входящие P2P-переводы любого типа.\n

        :param operation_types: Тип операций
        :param label: string.
        Отбор платежей по значению метки. Выбираются платежи, у которых указано заданное значение параметра label вызова request-payment.
        :param start_date: datetime	Вывести операции от момента времени (операции, равные start_date, или более поздние).
        Если параметр отсутствует, выводятся все операции.
        :param end_date: datetime	Вывести операции до момента времени (операции более ранние, чем end_date).
         Если параметр отсутствует, выводятся все операции.
        :param start_record: string	Если параметр присутствует, то будут отображены операции, начиная с номера start_record.
         Операции нумеруются с 0. Подробнее про постраничный вывод списка
        :param records:	int	Количество запрашиваемых записей истории операций. Допустимые значения: от 1 до 100, по умолчанию — 30.
        """
        headers = self._auth_token(parse_headers(**self.__content_and_auth))

        if records <= 0 or records > 100:
            raise InvalidData(
                'Неверное количество записей. '
                'Кол-во записей, которые можно запросить, находиться в диапазоне от 1 до 100 включительно'
            )

        data = {
            'records': records,
        }

        if operation_types:
            if all(isinstance(operation_type, OperationType) for operation_type in operation_types):
                data.update({'type': ' '.join([operation_type.value for operation_type in operation_types])})

        if isinstance(start_record, int):
            if start_record < 0:
                raise InvalidData('Укажите позитивное число')
            data.update({'start_record': start_record})

        data.update({'label': label}) if isinstance(label, str) else None
        if start_date:
            if not isinstance(start_date, datetime):
                raise InvalidData('Параметр start_date был передан неправильным типом данных')
            data.update({'from': datetime_to_str_in_iso(start_date)})

        if end_date:
            if not isinstance(end_date, datetime):
                raise InvalidData('Параметр end_date был передан неправильным типом данных')
            data.update({'till': datetime_to_str_in_iso(end_date)})

        async for response in self._parser.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/operation-history',
                method='POST',
                headers=headers,
                data=data,
                get_json=True
        ):
            return self._formatter.format_objects(
                iterable_obj=response.response_data.get('operations'),
                obj=Operation,
                transfers=OPERATION_TRANSFER
            )

    async def operation_details(self, operation_id: str):
        """
        Позволяет получить детальную информацию об операции из истории.
        Требуемые права токена: operation-details.

        :param operation_id: Идентификатор операции
        """
        headers = self._auth_token(parse_headers(**self.__content_and_auth))
        payload = {
            'operation_id': operation_id
        }
        async for response in self._parser.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/operation-details',
                headers=headers,
                data=payload
        ):
            return response.response_data


@measure_time
async def main():
    wallet = YooMoney(
        api_access_token=TOKEN
    )
    history = await wallet.get_operation_history(
        records=5,
        operation_types=[OperationType.PAYMENT],
    )
    print(history)


if __name__ == '__main__':
    asyncio.run(main())
