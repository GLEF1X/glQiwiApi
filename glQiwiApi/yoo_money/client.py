"""
Provides effortless work with YooMoney API using asynchronous requests.

"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Union, Optional, Tuple, cast

from glQiwiApi.core import (
    RequestManager,
    ToolsMixin,
    ContextInstanceMixin
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
from glQiwiApi.types.yoomoney_types.types import Card
from glQiwiApi.utils.api_helper import parse_auth_link, parse_headers, datetime_to_str_in_iso, \
    simple_multiply_parse, check_params, parse_amount
from glQiwiApi.utils.errors import NoUrlFound, InvalidData
from glQiwiApi.yoo_money.settings import YooMoneyRouter


class YooMoneyAPI(ToolsMixin, ContextInstanceMixin["YooMoneyAPI"]):
    """
    Класс, реализующий обработку запросов к YooMoney
    Удобен он тем, что не просто отдает json подобные объекты,
    а всё это конвертирует в pydantic модели.
    Для работы с данным классом, необходимо зарегистрировать токен,
    используя гайд на официальном github проекта

    """

    __slots__ = ("api_access_token", "_requests", "_router")

    def __init__(
            self,
            api_access_token: str,
            without_context: bool = False,
            cache_time: Union[float, int] = DEFAULT_CACHE_TIME,
            proxy: Optional[Any] = None
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
        self._router = YooMoneyRouter()
        self._requests = RequestManager(
            without_context=without_context,
            messages=self._router.config.ERROR_CODE_NUMBERS,
            cache_time=cache_time,
            proxy=proxy
        )

        self.set_current(self)

    def _auth_token(self, headers: dict) -> Dict[Any, Any]:
        headers['Authorization'] = headers['Authorization'].format(
            token=self.api_access_token
        )
        return headers

    @property
    def request_manager(self) -> RequestManager:
        return self._requests

    @classmethod
    async def build_url_for_auth(
            cls,
            scope: List[str],
            client_id: str,
            redirect_uri: str = 'https://example.com'
    ) -> Optional[str]:
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
        router = YooMoneyRouter()
        headers = parse_headers()
        params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': " ".join(scope)
        }
        response = await RequestManager(without_context=True, messages=router.config.ERROR_CODE_NUMBERS).make_request(
            router.build_url("BUILD_URL_FOR_AUTH"),
            "POST",
            headers=headers,
            data=params
        )
        try:
            return parse_auth_link(response)
        except IndexError:
            raise NoUrlFound('Не удалось найти ссылку для авторизации в ответе от апи, проверьте значение client_id')

    @classmethod
    async def get_access_token(
            cls,
            code: str,
            client_id: str,
            redirect_uri: str = 'https://example.com',
            client_secret: Optional[str] = None
    ) -> str:
        """
        Метод для получения токена для запросов к YooMoney API

        :param code: временный код, который был получен в методе base_authorize
        :param client_id: идентификатор приложения, тип string
        :param redirect_uri: воронка, куда попадет временный код,
         который нужен для получения основного токена
        :param client_secret: Секретное слово для проверки подлинности приложения.
         Указывается, если сервис зарегистрирован с проверкой подлинности.
        :return: YooMoney API TOKEN
        """
        router = YooMoneyRouter()
        headers = parse_headers(content_json=True)
        params = {
            'code': code,
            'client_id': client_id,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'client_secret': client_secret
        }
        response = await RequestManager(without_context=True, messages=router.config.ERROR_CODE_NUMBERS).make_request(
            router.build_url("GET_ACCESS_TOKEN"), "POST", headers=headers, data=params
        )
        return cast(str, response.get('access_token'))

    async def revoke_api_token(self) -> Optional[Dict[str, bool]]:
        """
        Метод для отмены прав токена, при этом все его права тоже пропадают
        Документация:
        https://yoomoney.ru/docs/wallet/using-api/authorization/revoke-access-token
        """
        headers = self._auth_token(parse_headers(auth=True))
        url = self._router.build_url("REVOKE_API_TOKEN")
        return await self.request_manager.make_request(url, "POST", headers=headers)

    @property
    async def account_info(self) -> AccountInfo:
        """
        Метод для получения информации об аккаунте пользователя
        Подробная документация:
        https://yoomoney.ru/docs/wallet/user-account/account-info

        :return: объект AccountInfo
        """
        headers = self._auth_token(parse_headers(**self._router.config.content_and_auth))
        url = self._router.build_url("ACCOUNT_INFO")
        response = await self.request_manager.make_request(url, "POST", headers=headers)
        return AccountInfo.parse_obj(response)

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
        headers = self._auth_token(parse_headers(**self._router.config.content_and_auth))

        if records <= 0 or records > 100:
            raise InvalidData(
                'Неверное количество записей. '
                'Кол-во записей, которые можно запросить,'
                ' находиться в диапазоне от 1 до 100 включительно'
            )
        data = {'records': records, 'label': label}
        if operation_types:
            if all(isinstance(operation_type, OperationType) for operation_type in operation_types):
                op_types = [operation_type.value for operation_type in operation_types]
                data.update({'type': ' '.join(op_types)})
        if isinstance(start_record, int):
            if start_record < 0:
                raise InvalidData('Укажите позитивное число')
            data.update({'start_record': start_record})
        if start_date:
            if not isinstance(start_date, datetime):
                raise InvalidData('Параметр start_date был передан неправильным типом данных')
            data.update({'from': datetime_to_str_in_iso(start_date, yoo_money_format=True)})

        if end_date:
            if not isinstance(end_date, datetime):
                raise InvalidData('Параметр end_date был передан неправильным типом данных')
            data.update({'till': datetime_to_str_in_iso(end_date, yoo_money_format=True)})
        url = self._router.build_url("TRANSACTIONS")
        response = await self.request_manager.make_request(url, "POST", headers=headers,
                                                           data=self.request_manager.filter_dict(data))
        return simple_multiply_parse(objects=cast(List[Any], response.get('operations')), model=Operation)

    async def transaction_info(self, operation_id: str) -> OperationDetails:
        """
        Позволяет получить детальную информацию об операции из истории.
        Требуемые права токена: operation-details.
        Более подробная документация:
        https://yoomoney.ru/docs/wallet/user-account/operation-details

        :param operation_id: Идентификатор операции
        """
        headers = self._auth_token(parse_headers(**self._router.config.content_and_auth))
        payload = {'operation_id': operation_id}
        url = self._router.build_url("TRANSACTION_INFO")
        response = await self.request_manager.make_request(url, "POST", data=payload, headers=headers)
        return OperationDetails.parse_obj(response)

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
        headers = self._auth_token(parse_headers(**self._router.config.content_and_auth))
        payload = {
            'pattern_id': pattern_id,
            'to': to_account,
            'amount_due': amount,
            'comment': comment_for_history,
            'message': comment_for_receiver,
            'expire_period': expire_period,
            'codepro': protect
        }
        url = self._router.build_url("PRE_PROCESS_PAYMENT")
        response = await self.request_manager.make_request(url, "POST", headers=headers, data=payload)
        return PreProcessPaymentResponse.parse_obj(response)

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
        url = self._router.build_url("PROCESS_PAYMENT")
        pre_payment = await self._pre_process_payment(
            to_account=to_account,
            amount=amount,
            comment_for_history=comment_for_history,
            comment_for_receiver=comment,
            expire_period=expire_period,
            protect=protect,
            pattern_id=pattern_id
        )
        headers = self._auth_token(parse_headers(**self._router.config.content_and_auth))
        payload = {
            'request_id': pre_payment.request_id,
            'money_source': 'wallet'
        }
        if money_source == 'card' and isinstance(pre_payment, PreProcessPaymentResponse):
            if pre_payment.money_source.cards.allowed == 'true':  # type: ignore
                if not isinstance(card_type, str):
                    cards = cast(Card, pre_payment.money_source.cards)  # type: ignore
                    payload.update({
                        'money_source': cards.items[0].item_id,
                        'csc': cvv2_code
                    })
                else:
                    cards = cast(Card, pre_payment.money_source.cards).items  # type: ignore
                    for card in cards:
                        if card.item_type == card_type:  # type: ignore
                            payload.update(
                                {
                                    'money_source': card.item_id,  # type: ignore
                                    'csc': cvv2_code
                                },
                            )
        response = await self.request_manager.make_request(url, "POST", headers=headers, data=payload)
        return Payment.parse_obj(response).initialize(pre_payment.protection_code)

    @property
    async def balance(self) -> float:
        """Метод для получения баланса на кошельке yoomoney"""
        return (await self.account_info).balance

    async def accept_incoming_transaction(self, operation_id: str, protection_code: str) -> IncomingTransaction:
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
        headers = self._auth_token(parse_headers(**self._router.config.content_and_auth))
        payload = {
            'operation_id': operation_id,
            'protection_code': protection_code
        }
        url = self._router.build_url("ACCEPT_INCOMING_TRANSFER")
        response = await self.request_manager.make_request(url, "POST", headers=headers, data=payload)
        return IncomingTransaction.parse_obj(response)

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
        headers = self._auth_token(parse_headers(**self._router.config.content_and_auth))
        url = self._router.build_url("INCOMING_TRANSFER_REJECT")
        return await self.request_manager.make_request(url, "POST", headers=headers,
                                                       data={'operation_id': operation_id})

    async def check_transaction(
            self,
            amount: Union[int, float],
            transaction_type: str = 'in',
            comment: Optional[str] = None,
            rows_num: int = 100,
            recipient: Optional[str] = None
    ) -> bool:
        """
        Метод для проверки транзакции.\n
        Данный метод использует self.transactions(rows_num=rows_num)
         для получения платежей.\n
        Для небольшой оптимизации вы можете уменьшить rows_num задав его,
        однако это не гарантирует правильный результат

        :param amount: сумма платежа
        :param transaction_type: тип платежа
        :param recipient: номер получателя
        :param rows_num: кол-во платежей, которое будет проверяться
        :param comment: комментарий, по которому будет проверяться транзакция
        :return: bool, есть ли такая транзакция в истории платежей
        """
        # Generate types of transactions for request
        types = [OperationType.DEPOSITION if transaction_type == 'in' else OperationType.PAYMENT]
        # Get transactions by params
        transactions = await self.transactions(operation_types=types, records=rows_num)
        tasks = [self.transaction_info(txn.operation_id) for txn in transactions]
        for detail in await asyncio.gather(*tasks):
            # Parse amount and comment,
            # because the parameters depend on the type of transaction
            amount_, comment_ = parse_amount(transaction_type, detail)
            checked = check_params(
                amount=amount,
                transaction_type=transaction_type,
                amount_=amount_,
                txn=detail
            )
            if checked:
                if detail.status == 'success':
                    if comment_ == comment and detail.sender == recipient:
                        return True
                    elif isinstance(comment, str) and isinstance(recipient, str):
                        continue
                    elif comment_ == comment:
                        return True

        return False
