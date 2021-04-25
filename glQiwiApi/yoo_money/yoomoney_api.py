from datetime import datetime
from typing import List, Dict, Any, Union, Optional, Tuple

from pydantic import ValidationError

import glQiwiApi.utils.basics as api_helper
from glQiwiApi.core import (
    AbstractPaymentWrapper,
    RequestManager,
    ToolsMixin
)
from glQiwiApi.types import (
    AccountInfo,
    OperationType,
    Operation,
    OperationDetails,
    PreProcessPaymentResponse,
    Payment,
    IncomingTransaction
)
from glQiwiApi.types.basics import DEFAULT_CACHE_TIME
from glQiwiApi.utils.exceptions import NoUrlFound, InvalidData
from glQiwiApi.yoo_money.basic_yoomoney_config import (
    BASE_YOOMONEY_URL,
    ERROR_CODE_NUMBERS,
    content_and_auth
)


class YooMoneyAPI(AbstractPaymentWrapper, ToolsMixin):
    """
    Класс, реализующий обработку запросов к YooMoney
    Удобен он тем, что не просто отдает json подобные объекты,
    а всё это конвертирует в python dataclasses.
    Для работы с данным классом, необходимо зарегистрировать токен,
    используя гайд на официальном github проекта

    """

    __slots__ = ("api_access_token", "_requests",)

    def __init__(
            self,
            api_access_token: str,
            without_context: bool = False,
            cache_time: Union[float, int] = DEFAULT_CACHE_TIME
    ) -> None:
        """
        Конструктор принимает токен, полученный из класс метода
         get_access_token
        и специальный аттрибут without_context,

        :param api_access_token: апи токен для запросов
        :param without_context: bool, указывающая будет
         ли объект класса "глобальной" переменной
         или будет использована в async with контексте
        :param cache_time: Время кэширование запросов в секундах,
         по умолчанию 0, соответственно,
         запрос не будет использовать кэш по дефолту, максимальное время
         кэширование 60 секунд
        """
        self.api_access_token = api_access_token
        self._requests = RequestManager(
            without_context=without_context,
            messages=ERROR_CODE_NUMBERS,
            cache_time=cache_time
        )

    def _auth_token(self, headers: dict) -> Dict[Any, Any]:
        headers['Authorization'] = headers['Authorization'].format(
            token=self.api_access_token
        )
        return headers

    @classmethod
    async def build_url_for_auth(
            cls,
            scope: List[str],
            client_id: str,
            redirect_uri: str = 'https://example.com'
    ) -> str:
        """
        Метод для получения ссылки для
        дальнейшей авторизации и получения токена

        :param scope: OAuth2-авторизации приложения пользователем,
         права передаются списком.
        :param client_id: идентификатор приложения, тип string
        :param redirect_uri: воронка, куда попадет временный код, который нужен
         для получения основного токена
        :return: ссылку, по которой нужно перейти
         и сделать авторизацию через логин/пароль
        """
        headers = api_helper.parse_headers()
        params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': " ".join(scope)
        }
        async for response in RequestManager(
                without_context=True,
                messages=ERROR_CODE_NUMBERS,
                cache_time=DEFAULT_CACHE_TIME
        ).fast().fetch(
            url=BASE_YOOMONEY_URL + '/oauth/authorize',
            headers=headers,
            data=params,
            method='POST'
        ):
            try:
                return api_helper.parse_auth_link(response.response_data)
            except IndexError:
                raise NoUrlFound(
                    'Не удалось найти ссылку для авторизации '
                    'в ответе от апи, проверьте client_id'
                )

    @classmethod
    async def get_access_token(
            cls,
            code: str,
            client_id: str,
            redirect_uri: str = 'https://example.com'
    ) -> str:
        """
        Метод для получения токена для запросов к YooMoney API

        :param code: временный код, который был получен в методе base_authorize
        :param client_id: идентификатор приложения, тип string
        :param redirect_uri: воронка, куда попадет временный код,
         который нужен для получения основного токена
        :return: YooMoney API TOKEN
        """
        headers = api_helper.parse_headers(content_json=True)
        params = {
            'code': code,
            'client_id': client_id,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        async for response in RequestManager(
                without_context=True,
                messages=ERROR_CODE_NUMBERS,
                cache_time=DEFAULT_CACHE_TIME
        ).fast().fetch(
            url=BASE_YOOMONEY_URL + '/oauth/token',
            headers=headers,
            data=params,
            method='POST',
            get_json=True
        ):
            return response.response_data.get('access_token')

    async def revoke_api_token(self) -> Optional[Dict[str, bool]]:
        """
        Метод для отмены прав токена, при этом все его права тоже пропадают
        Документация:
        https://yoomoney.ru/docs/wallet/using-api/authorization/revoke-access-token
        """
        headers = self._auth_token(
            api_helper.parse_headers(auth=True)
        )
        async for response in self._requests.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/revoke',
                method='POST',
                headers=headers
        ):
            if response.ok:
                return {'success': True}

    async def account_info(self) -> AccountInfo:
        """
        Метод для получения информации об аккаунте пользователя
        Подробная документация:
        https://yoomoney.ru/docs/wallet/user-account/account-info

        :return: объект AccountInfo
        """
        headers = self._auth_token(
            api_helper.parse_headers(
                **content_and_auth
            )
        )
        async for response in self._requests.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/account-info',
                headers=headers,
                method='POST'
        ):
            return AccountInfo.parse_raw(response.response_data)

    async def transactions(
            self,
            operation_types: Optional[
                Union[List[OperationType], Tuple[OperationType, ...]]
            ] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            start_record: Optional[int] = None,
            records: int = 30,
            label: Optional[Union[str, int]] = None
    ) -> List[Operation]:
        """
        Подробная документация:
        https://yoomoney.ru/docs/wallet/user-account/operation-history\n
        Метод позволяет просматривать историю операций (полностью или частично)
        в постраничном режиме.\n
        Записи истории выдаются в обратном хронологическом порядке:
        от последних к более ранним.\n
        Перечень типов операций, которые требуется отобразить.\n
        Возможные значения:
        DEPOSITION — пополнение счета (приход);\n
        PAYMENT — платежи со счета (расход);\n
        INCOMING(incoming-transfers-unaccepted) —
         непринятые входящие P2P-переводы любого типа.\n

        :param operation_types: Тип операций
        :param label: string.
         Отбор платежей по значению метки.
         Выбираются платежи, у которых указано заданное значение параметра
         label вызова request-payment.
        :param start_date: datetime	Вывести операции от момента времени
         (операции, равные start_date, или более поздние)
         Если параметр отсутствует, выводятся все операции.
        :param end_date: datetime	Вывести операции до момента времени
         (операции более ранние, чем end_date).
         Если параметр отсутствует, выводятся все операции.
        :param start_record: string
         Если параметр присутствует, то будут отображены операции, начиная
          с номера start_record.
         Операции нумеруются с 0. Подробнее про постраничный вывод списка
        :param records:	int	Количество запрашиваемых записей истории операций.
         Допустимые значения: от 1 до 100, по умолчанию — 30.
        """
        headers = self._auth_token(
            api_helper.parse_headers(**content_and_auth)
        )

        if records <= 0 or records > 100:
            raise InvalidData(
                'Неверное количество записей. '
                'Кол-во записей, которые можно запросить,'
                ' находиться в диапазоне от 1 до 100 включительно'
            )

        data = {
            'records': records,
            'label': label
        }

        if operation_types:
            if all(
                    isinstance(
                        operation_type, OperationType
                    ) for operation_type in operation_types
            ):
                op_types = [
                    operation_type.value for operation_type in operation_types
                ]
                data.update({'type': ' '.join(
                    op_types)}
                )

        if isinstance(start_record, int):
            if start_record < 0:
                raise InvalidData('Укажите позитивное число')
            data.update({'start_record': start_record})

        if start_date:
            if not isinstance(start_date, datetime):
                raise InvalidData(
                    'Параметр start_date был передан неправильным типом данных'
                )
            data.update({'from': api_helper.datetime_to_str_in_iso(
                start_date, True
            )})

        if end_date:
            if not isinstance(end_date, datetime):
                raise InvalidData(
                    'Параметр end_date был передан неправильным типом данных'
                )
            data.update({'till': api_helper.datetime_to_str_in_iso(
                end_date, True
            )})

        async for response in self._requests.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/operation-history',
                method='POST',
                headers=headers,
                data=self._requests.filter_dict(data),
                get_json=True
        ):
            return api_helper.multiply_objects_parse(
                lst_of_objects=response.response_data.get('operations'),
                model=Operation
            )

    async def transaction_info(self, operation_id: str) -> OperationDetails:
        """
        Позволяет получить детальную информацию об операции из истории.
        Требуемые права токена: operation-details.
        Более подробная документация:
        https://yoomoney.ru/docs/wallet/user-account/operation-details

        :param operation_id: Идентификатор операции
        """
        headers = self._auth_token(api_helper.parse_headers(
            **content_and_auth)
        )
        payload = {
            'operation_id': operation_id
        }
        async for response in self._requests.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/operation-details',
                headers=headers,
                data=payload
        ):
            return OperationDetails.parse_raw(response.response_data)

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
        Более подробная документация:
        https://yoomoney.ru/docs/wallet/process-payments/request-payment\n
        Создание платежа, проверка параметров и возможности приема
        платежа магазином или перевода средств на счет пользователя ЮMoney.\n
        Данный метод не рекомендуется использовать напрямую, гораздо
        проще использовать send.
        Требуемые права токена:
        to-account («идентификатор получателя», «тип идентификатора»)

        :param pattern_id: Идентификатор шаблона платежа
        :param to_account: string Идентификатор получателя перевода
         (номер счета, номер телефона или email).
        :param amount: Сумма к получению
         (придет на счет получателя счет после оплаты).
        :param comment_for_history: Комментарий к переводу,
         отображается в истории отправителя.
        :param comment_for_receiver:	string	Комментарий к переводу,
         отображается получателю.
        :param protect: Значение параметра true — признак того,
         что перевод защищен кодом протекции.
         По умолчанию параметр отсутствует (обычный перевод).
        :param expire_period: Число дней, в течении которых:
            получатель перевода может ввести код протекции
            и получить перевод на свой счет,
            получатель перевода до востребования может получить перевод.
            Значение параметра должно находиться в интервале от 1 до 365.
            Необязательный параметр. По умолчанию 1.
        """
        headers = self._auth_token(
            api_helper.parse_headers(**content_and_auth))
        payload = {
            'pattern_id': pattern_id,
            'to': to_account,
            'amount_due': amount,
            'comment': comment_for_history,
            'message': comment_for_receiver,
            'expire_period': expire_period,
            'codepro': protect
        }
        async for response in self._requests.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/request-payment',
                headers=headers,
                data=payload
        ):
            try:
                return PreProcessPaymentResponse.parse_raw(
                    response.response_data
                )
            except ValidationError:
                msg = "Недостаточно денег для перевода или ошибка сервиса"
                self._requests.raise_exception(
                    status_code=400,
                    message=msg
                )

    async def send(
            self,
            to_account: str,
            amount: Union[int, float],
            money_source: str = 'wallet',
            pattern_id: str = 'p2p',
            cvv2_code: str = '',
            card_type: Optional[str] = None,
            protect: bool = False,
            comment_for_history: Optional[str] = None,
            comment: Optional[str] = None,
            expire_period: int = 1
    ) -> Payment:
        """
        Метод для отправки денег на аккаунт или карту другого человека.
        Данная функция делает сразу 2 запроса, из-за этого
         вы можете почувствовать небольшую потерю производительности,
          вы можете использовать метод
        _pre_process_payment и получать объект PreProcessPaymentResponse,
        в котором есть информация о ещё неподтвержденном платеже\n
        Более подробная документация:
        https://yoomoney.ru/docs/wallet/process-payments/process-payment

        :param pattern_id: Идентификатор шаблона платежа
        :param to_account: string Идентификатор получателя перевода
         (номер счета, номер телефона или email).
        :param amount: Сумма к получению
         (придет на счет получателя счет после оплаты). МИНИМАЛЬНАЯ СУММА 2.
        :param money_source: Запрашиваемый метод проведения платежа.
         wallet — со счета пользователя, если вы хотите использовать card,
         тогда нужно будет передать card_type
         для поиска карты в списке ваших банковских карт,
         а также опционально cvv2 код для проведения платежа
        :param comment_for_history: Комментарий к переводу,
         отображается в истории отправителя.
        :param card_type: Тип банковской карты, нужно заполнять,
         только если вы хотите списать средства с вашей карты
        :param cvv2_code: опционально, может быть не передан, однако,
         если для оплаты картой это требуется,
         параметр стоит передавать
        :param comment:	Комментарий к переводу, отображается получателю.
        :param protect: Значение параметра true — признак того,
         что перевод защищен кодом протекции.
         По умолчанию параметр отсутствует (обычный перевод).
        :param expire_period: Число дней, в течении которых:
            получатель перевода может ввести код протекции и
            получить перевод на свой счет,
            получатель перевода до востребования может получить перевод.
            Значение параметра должно находиться в интервале от 1 до 365.
            Необязательный параметр. По умолчанию 1.
        """
        if amount < 2:
            raise InvalidData(
                'Введите сумму, которая больше минимальной(2 и выше)'
            )
        pre_payment = await self._pre_process_payment(
            to_account=to_account,
            amount=amount,
            comment_for_history=comment_for_history,
            comment_for_receiver=comment,
            expire_period=expire_period,
            protect=protect,
            pattern_id=pattern_id
        )

        headers = self._auth_token(
            api_helper.parse_headers(**content_and_auth))

        payload = {
            'request_id': pre_payment.request_id,
            'money_source': 'wallet'
        }
        expression = isinstance(pre_payment, PreProcessPaymentResponse)
        if money_source == 'card' and expression:
            if pre_payment.money_source.cards.allowed == 'true':
                if not isinstance(card_type, str):
                    cards = pre_payment.money_source.cards
                    payload.update({
                        'money_source': cards.items[0].item_id,
                        'csc': cvv2_code
                    })
                else:
                    cards = pre_payment.money_source.cards.items
                    for card in cards:
                        if card.item_type == card_type:
                            payload.update(
                                {
                                    'money_source': card.item_id,
                                    'csc': cvv2_code
                                },
                            )
        async for response in self._requests.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/process-payment',
                method='POST',
                headers=headers,
                data=payload
        ):
            return Payment.parse_raw(
                response.response_data
            ).initialize(pre_payment.protection_code)

    async def get_balance(self) -> Optional[Union[float, int]]:
        """Метод для получения баланса на кошельке yoomoney"""
        return (await self.account_info()).balance

    async def accept_incoming_transaction(
            self,
            operation_id: str,
            protection_code: str
    ) -> IncomingTransaction:
        """
        Прием входящих переводов, защищенных кодом протекции,
        если вы передали в метод send параметр protect
        Количество попыток приема
        входящего перевода с кодом протекции ограничено.
        При исчерпании количества попыток, перевод автоматически отвергается
        (перевод возвращается отправителю).
        Более подробная документация:
        https://yoomoney.ru/docs/wallet/process-payments/incoming-transfer-accept

        :param operation_id: Идентификатор операции,
         значение параметра operation_id ответа метода history()
        :param protection_code: Код протекции. Строка из 4-х десятичных цифр.
         Указывается для входящего перевода, защищенного кодом протекции.
         Для переводов до востребования отсутствует.
        """
        headers = self._auth_token(
            api_helper.parse_headers(**content_and_auth))
        payload = {
            'operation_id': operation_id,
            'protection_code': protection_code
        }
        async for response in self._requests.fast().fetch(
                url=BASE_YOOMONEY_URL + '/api/incoming-transfer-accept',
                headers=headers,
                data=payload,
                method='POST',
                get_json=True
        ):
            return IncomingTransaction.parse_raw(
                response.response_data
            )

    async def reject_transaction(self, operation_id: str) -> Dict[str, str]:
        """
        Отмена входящих переводов, защищенных кодом протекции, если вы передали
         в метод send параметр protect,
        и переводов до востребования. \n
        При отмене перевода он возвращается отправителю. \n
        Требуемые права токена: incoming-transfers

        Более подробная документация:
        https://yoomoney.ru/docs/wallet/process-payments/incoming-transfer-reject

        :param operation_id: Идентификатор операции, значение параметра
         operation_id ответа метода history().
        :return: словарь в json формате с ответом от апи
        """
        headers = self._auth_token(
            api_helper.parse_headers(**content_and_auth))
        async for response in self._requests.fast().fetch(
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
            transaction_type: str = 'in',
            comment: Optional[str] = None,
            rows_num: int = 100,
            sender_number: Optional[str] = None
    ) -> bool:
        """
        Метод для проверки транзакции.\n
        Данный метод использует self.transactions(rows_num=rows_num)
         для получения платежей.\n
        Для небольшой оптимизации вы можете уменьшить rows_num задав его,
        однако это не гарантирует правильный результат

        :param amount: сумма платежа
        :param transaction_type: тип платежа
        :param sender_number: номер получателя
        :param rows_num: кол-во платежей, которое будет проверяться
        :param comment: комментарий, по которому будет проверяться транзакция
        :return: bool, есть ли такая транзакция в истории платежей
        """
        # Generate types of transactions for request
        types = [
            OperationType.DEPOSITION if transaction_type == 'in' else OperationType.PAYMENT]
        # Get transactions by params
        transactions = await self.transactions(
            operation_types=types,
            records=rows_num
        )
        for txn in transactions:
            # Get details of transaction to check it later
            detail = await self.transaction_info(txn.operation_id)

            # Parse amount and comment,
            # because the parameters depend on the type of transaction
            amount_, comment_ = api_helper.parse_amount(
                transaction_type,
                detail
            )
            checked = api_helper.check_params(
                amount=amount,
                transaction_type=transaction_type,
                amount_=amount_,
                txn=detail
            )
            if checked:
                if txn.status == 'success':
                    if comment_ == comment and detail.sender == sender_number:
                        return True
                    elif isinstance(comment, str) and isinstance(
                            sender_number,
                            str):
                        continue
                    elif comment_ == comment:
                        return True

        return False
