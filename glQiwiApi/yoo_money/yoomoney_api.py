from datetime import datetime
from functools import lru_cache
from typing import List, Dict, Any, Union, Optional, Tuple, Literal

from glQiwiApi import HttpXParser
from glQiwiApi.data import AccountInfo, OperationType, Operation, OperationDetails, PreProcessPaymentResponse, \
    Payment, IncomingTransaction
from glQiwiApi.exceptions import NoUrlFound, InvalidData
from glQiwiApi.utils import parse_auth_link, parse_headers, DataFormatter, datetime_to_str_in_iso
from glQiwiApi.yoo_money.basic_yoomoney_config import *


class YooMoneyAPI(object):
    """
    Класс, реализующий обработку запросов к YooMoney, используя основной класс HttpXParser,
    удобен он тем, что не просто отдает json подобные объекты, а всё это конвертирует в python датаклассы.
    Для работы с данным классом, необходимо загестрировать токен по такому
    """

    def __init__(self, api_access_token: str) -> None:
        """
        Конструктор принимает только токен, полученный из класс метода get_access_token() этого же класса

        :param api_access_token: апи токен для запросов
        """
        self.api_access_token = api_access_token
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

        :param code: временный код, который был получен в методе base_authorize()
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

    async def revoke_api_token(self) -> Optional[Dict[str, bool]]:
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
            if response.ok:
                return {'success': True}

    @lru_cache
    async def account_info(self) -> AccountInfo:
        """
        Метод для получения информации об аккаунте пользователя
        Подробная документация: https://yoomoney.ru/docs/wallet/user-account/account-info

        :return: объект AccountInfo
        """
        headers = self._auth_token(parse_headers(**content_and_auth))
        async for response in self._parser.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/account-info',
                headers=headers,
                method='POST'
        ):
            try:
                return self._formatter.format_objects(
                    iterable_obj=(response.response_data,),
                    obj=AccountInfo,
                )[0]
            except IndexError:
                raise InvalidData('Cannot fetch account info, check your token')

    async def transactions(
            self,
            operation_types: Optional[Union[List[OperationType], Tuple[OperationType]]] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            start_record: Optional[int] = None,
            records: int = 30,
            label: Optional[Union[str, int]] = None
    ) -> List[Operation]:
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
        Отбор платежей по значению метки.
         Выбираются платежи, у которых указано заданное значение параметра label вызова request-payment.
        :param start_date: datetime	Вывести операции от момента времени (операции, равные start_date, или более поздние)
        Если параметр отсутствует, выводятся все операции.
        :param end_date: datetime	Вывести операции до момента времени (операции более ранние, чем end_date).
         Если параметр отсутствует, выводятся все операции.
        :param start_record: string
         Если параметр присутствует, то будут отображены операции, начиная с номера start_record.
         Операции нумеруются с 0. Подробнее про постраничный вывод списка
        :param records:	int	Количество запрашиваемых записей истории операций.
         Допустимые значения: от 1 до 100, по умолчанию — 30.
        """
        headers = self._auth_token(parse_headers(**content_and_auth))

        if records <= 0 or records > 100:
            raise InvalidData(
                'Неверное количество записей. '
                'Кол-во записей, которые можно запросить, находиться в диапазоне от 1 до 100 включительно'
            )

        data = {
            'records': records
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
            data.update({'from': datetime_to_str_in_iso(start_date, yoo_money_format=True)})

        if end_date:
            if not isinstance(end_date, datetime):
                raise InvalidData('Параметр end_date был передан неправильным типом данных')
            data.update({'till': datetime_to_str_in_iso(end_date, yoo_money_format=True)})

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

    async def get_transaction_info(self, operation_id: str) -> OperationDetails:
        """
        Позволяет получить детальную информацию об операции из истории.
        Требуемые права токена: operation-details.
        Более подробная документация: https://yoomoney.ru/docs/wallet/user-account/operation-details

        :param operation_id: Идентификатор операции
        """
        headers = self._auth_token(parse_headers(**content_and_auth))
        payload = {
            'operation_id': operation_id
        }
        async for response in self._parser.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/operation-details',
                headers=headers,
                data=payload
        ):
            try:
                obj = self._formatter.format_objects(
                    iterable_obj=(response.response_data,),
                    obj=OperationDetails,
                    transfers=OPERATION_TRANSFER
                )[0]
                if obj.error:
                    raise IndexError()
                return obj
            except (IndexError, AttributeError):
                raise ConnectionError(
                    'Не удалось получить объект, проверьте токен, который вы передаете в конструктор класса'
                )

    async def _pre_process_payment(
            self,
            to_account: str,
            amount: Union[int, float],
            pattern_id: str = 'p2p',
            comment_for_history: Optional[str] = None,
            comment_for_receiver: Optional[str] = None,
            protect: bool = False,
            expire_period: int = 1
    ) -> PreProcessPaymentResponse:
        """
        Более подробная документация: https://yoomoney.ru/docs/wallet/process-payments/request-payment\n
        Создание платежа, проверка параметров и возможности приема платежа магазином или перевода средств
        на счет пользователя ЮMoney.\n
        Данный метод не рекомендуется использовать напрямую, гораздо проще использовать send.
        Требуемые права токена:
        payment.to-account («идентификатор получателя», «тип идентификатора») или payment-p2p.

        :param pattern_id: Идентификатор шаблона платежа
        :param to_account: string Идентификатор получателя перевода (номер счета, номер телефона или email).
        :param amount: Сумма к получению (придет на счет получателя счет после оплаты).
        :param comment_for_history: Комментарий к переводу, отображается в истории отправителя.
        :param comment_for_receiver:	string	Комментарий к переводу, отображается получателю.
        :param protect: Значение параметра true — признак того, что перевод защищен кодом протекции.
         По умолчанию параметр отсутствует (обычный перевод).
        :param expire_period: Число дней, в течении которых:
            получатель перевода может ввести код протекции и получить перевод на свой счет,
            получатель перевода до востребования может получить перевод.
            Значение параметра должно находиться в интервале от 1 до 365. Необязательный параметр. По умолчанию 1.
        """
        headers = self._auth_token(parse_headers(**content_and_auth))
        payload = {
            'pattern_id': pattern_id,
            'to': to_account,
            'amount_due': amount,
            'comment': comment_for_history,
            'message': comment_for_receiver,
            'expire_period': expire_period,
            'codepro': protect
        }
        async for response in self._parser.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/request-payment',
                headers=headers,
                data=payload
        ):
            try:
                obj = self._formatter.format_objects(
                    iterable_obj=(response.response_data,),
                    obj=PreProcessPaymentResponse
                )[0]
                if obj.status != 'success':
                    raise IndexError()
                return obj
            except (IndexError, AttributeError):
                raise ConnectionError(
                    'Не удалось создать pre_payment запрос, проверьте переданные параметры и попробуйте ещё раз'
                )

    async def send(
            self,
            to_account: str,
            amount: Union[int, float],
            money_source: Literal['wallet', 'card'] = 'wallet',
            pattern_id: str = 'p2p',
            cvv2_code: str = '',
            card_type: Optional[Literal['Visa', 'MasterCard', 'American Express', 'JCB']] = None,
            protect: bool = False,
            comment_for_history: Optional[str] = None,
            comment: Optional[str] = None,
            expire_period: int = 1
    ) -> Payment:
        """
        Метод для отправки денег на аккаунт или карту другого человека. Данная функция делает сразу 2 запроса,
        из-за этого вы можете почувствовать небольшую потерю производительности, вы можете использовать метод
        _pre_process_payment и получать объект PreProcessPaymentResponse,
        в котором есть информация о ещё неподтвержденном платеже\n
        Более подробная документация: https://yoomoney.ru/docs/wallet/process-payments/process-payment

        :param pattern_id: Идентификатор шаблона платежа
        :param to_account: string Идентификатор получателя перевода (номер счета, номер телефона или email).
        :param amount: Сумма к получению (придет на счет получателя счет после оплаты). МИНИМАЛЬНАЯ СУММА 2.
        :param money_source: Запрашиваемый метод проведения платежа.
         wallet — со счета пользователя, если вы хотите использовать card,
         тогда нужно будет передать card_type для поиска карты в списке ваших банковских карт,
         а также опционально cvv2 код для проведения платежа
        :param comment_for_history: Комментарий к переводу, отображается в истории отправителя.
        :param card_type: Тип банковской карты, нужно заполнять, только если вы хотите списать средства с вашей карты
        :param cvv2_code: опционально, может быть не передан, однако, если для оплаты картой это требуется,
         параметр стоит передавать
        :param comment:	Комментарий к переводу, отображается получателю.
        :param protect: Значение параметра true — признак того, что перевод защищен кодом протекции.
         По умолчанию параметр отсутствует (обычный перевод).
        :param expire_period: Число дней, в течении которых:
            получатель перевода может ввести код протекции и получить перевод на свой счет,
            получатель перевода до востребования может получить перевод.
            Значение параметра должно находиться в интервале от 1 до 365. Необязательный параметр. По умолчанию 1.
        """
        if amount < 2:
            raise InvalidData('Введите сумму, которая больше минимальной(2 и выше)')
        pre_payment = await self._pre_process_payment(
            to_account=to_account,
            amount=amount,
            comment_for_history=comment_for_history,
            comment_for_receiver=comment,
            expire_period=expire_period,
            protect=protect,
            pattern_id=pattern_id
        )
        headers = self._auth_token(parse_headers(**content_and_auth))

        payload = {
            'request_id': pre_payment.request_id,
            'money_source': 'wallet'
        }

        if money_source == 'card' and isinstance(pre_payment, PreProcessPaymentResponse):
            if pre_payment.money_source.get('cards').get('allowed') == 'true':
                if not card_type:
                    payload.update({
                        'money_source': pre_payment.money_source.get('cards').get('items')[0].get('id'),
                        'csc': cvv2_code
                    })
                else:
                    cards = pre_payment.money_source.get('cards').get('items')
                    for card in cards:
                        if card.get('type') == card_type:
                            payload.update(
                                {'money_source': card.get('id'), 'csc': cvv2_code},
                            )
        async for response in self._parser.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/process-payment',
                method='POST',
                headers=headers,
                data=payload
        ):
            try:
                obj = self._formatter.format_objects(
                    iterable_obj=(response.response_data,),
                    obj=Payment
                )[0]
                obj.protection_code = pre_payment.protection_code
                return obj
            except (IndexError, AttributeError):
                raise ConnectionError(
                    'Не удалось создать запрос на перевод средств, проверьте переданные параметры и попробуйте ещё раз'
                )

    @property
    async def balance(self) -> Optional[Union[float, int]]:
        """Метод для получения баланса на кошельке юмани"""
        return (await self.account_info()).balance

    async def accept_incoming_transaction(
            self,
            operation_id: str,
            protection_code: str
    ) -> IncomingTransaction:
        """
        Прием входящих переводов, защищенных кодом протекции, если вы передали в метод send параметр protect,
        и переводов до востребования.
        Количество попыток приема входящего перевода с кодом протекции ограничено.
        При исчерпании количества попыток, перевод автоматически отвергается (перевод возвращается отправителю).
        Более подробная документация: https://yoomoney.ru/docs/wallet/process-payments/incoming-transfer-accept

        :param operation_id: Идентификатор операции, значение параметра operation_id ответа метода history()
        :param protection_code: Код протекции. Строка из 4-х десятичных цифр.
         Указывается для входящего перевода, защищенного кодом протекции. Для переводов до востребования отсутствует.
        """
        headers = self._auth_token(parse_headers(**content_and_auth))
        payload = {
            'operation_id': operation_id,
            'protection_code': protection_code
        }
        async for response in self._parser.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/incoming-transfer-accept',
                headers=headers,
                data=payload,
                method='POST',
                get_json=True
        ):
            try:
                return self._formatter.format_objects(
                    iterable_obj=(response.response_data,),
                    obj=IncomingTransaction
                )[0]
            except IndexError:
                raise ConnectionError('Такая транзакция не найдена или были переданы невалид данные')

    async def reject_transaction(self, operation_id: str) -> Dict[str, str]:
        """
        Отмена входящих переводов, защищенных кодом протекции, если вы передали в метод send параметр protect,
        и переводов до востребования. \n
        При отмене перевода он возвращается отправителю. \n
        Требуемые права токена: incoming-transfers

        Более подробная документация: https://yoomoney.ru/docs/wallet/process-payments/incoming-transfer-reject

        :param operation_id: Идентификатор операции, значение параметра operation_id ответа метода history().
        :return: словарь в json формате с ответом от апи
        """
        headers = self._auth_token(parse_headers(**content_and_auth))
        async for response in self._parser.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/incoming-transfer-reject',
                headers=headers,
                data={'operation_id': operation_id},
                method='POST',
                get_json=True
        ):
            return response.response_data

    async def check_transaction(
            self,
            amount: Union[int, float],
            transaction_type: Literal['in', 'out'] = 'in',
            comment: Optional[str] = None,
            rows_num: int = 100,
            sender_number: Optional[str] = None
    ) -> bool:
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
        transactions = await self.transactions(
            operation_types=[OperationType.DEPOSITION if transaction_type == 'in' else OperationType.PAYMENT],
            records=rows_num
        )

        for transaction in transactions:
            details_transaction = await self.get_transaction_info(transaction.operation_id)
            detail_amount = details_transaction.amount if transaction_type == 'in' else details_transaction.amount_due
            detail_comment = details_transaction.comment if transaction_type == 'in' else details_transaction.message
            if detail_amount >= amount and details_transaction.direction == transaction_type:
                if transaction.status == 'success':
                    if detail_comment == comment and details_transaction.sender == sender_number:
                        return True
                    elif isinstance(comment, str) and isinstance(sender_number, str):
                        continue
                    elif detail_comment == comment:
                        return True

        return False
