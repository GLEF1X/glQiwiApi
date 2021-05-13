import pathlib
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Union, Optional, Dict, List, Any, MutableMapping

from aiohttp import ClientSession

from glQiwiApi.core import RequestManager, ToolsMixin
from glQiwiApi.core.web_hooks import dispatcher
from glQiwiApi.qiwi.mixins import (
    QiwiKassaMixin,
    QiwiMasterMixin,
    HistoryPollingMixin,
    QiwiWebHookMixin,
    QiwiPaymentsMixin
)
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
    Restriction
)
from glQiwiApi.types.basics import DEFAULT_CACHE_TIME
from glQiwiApi.utils import basics as api_helper
from glQiwiApi.utils.exceptions import InvalidData


class QiwiWrapper(
    QiwiWebHookMixin, QiwiPaymentsMixin,
    QiwiMasterMixin, ToolsMixin,
    HistoryPollingMixin, QiwiKassaMixin
):
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
        '_router',
        '_p2p_router',
        'dispatcher'
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

        if not hasattr(self, "phone_number"):
            raise InvalidData("Invalid phone number value")

        self._router: QiwiRouter = QiwiRouter()
        self._p2p_router: QiwiKassaRouter = QiwiKassaRouter()
        self._requests: RequestManager = RequestManager(
            without_context=without_context,
            messages=self._router.config.ERROR_CODE_NUMBERS,
            cache_time=cache_time
        )
        self.api_access_token = api_access_token
        self.secret_p2p = secret_p2p
        # Special dispatcher to manage handlers and events from polling
        # or webhooks
        self.dispatcher = dispatcher.Dispatcher(
            loop=api_helper.take_event_loop(),
            wallet=self
        )
        super(QiwiWrapper, self).__init__(
            router=self._router, requests_manager=self._requests,
            secret_p2p=self.secret_p2p
        )

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
    def session(self) -> Optional[ClientSession]:
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
                }
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
                method='GET'
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
                headers=headers
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
                headers=headers
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
                headers=headers
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
                params=data
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
                method='GET'
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
                json={'defaultAccount': True}
        ):
            return response
