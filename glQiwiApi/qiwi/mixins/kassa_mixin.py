import uuid
from copy import deepcopy
from datetime import datetime
from typing import Union, Optional, Dict, List, Any, MutableMapping

from glQiwiApi.core import constants
from glQiwiApi.core.abstracts import AbstractRouter
from glQiwiApi.types import Bill, BillError, OptionalSum
from glQiwiApi.types.qiwi_types.bill import RefundBill, P2PKeys
from glQiwiApi.utils import basics as api_helper
from glQiwiApi.utils.exceptions import InvalidData


class QiwiKassaMixin:

    def __init__(
            self,
            p2p_router: AbstractRouter,
            default_router: AbstractRouter,
            requests_manager: Any,
            secret_p2p: str
    ):
        self._router = default_router
        self._p2p_router = p2p_router
        self._requests = requests_manager
        self.secret_p2p = secret_p2p

    def _auth_token(
            self,
            headers: MutableMapping,
            p2p: bool = False
    ) -> MutableMapping:
        ...

    async def reject_p2p_bill(self, bill_id: str) -> Bill:
        """
        Метод для отмены транзакции.

        :param bill_id: номер p2p транзакции
        :return: Bill obj
        """
        if not self.secret_p2p:
            raise InvalidData('Не задан p2p токен')
        data = deepcopy(self._p2p_router.config.P2P_DATA)
        headers = self._auth_token(data.headers, p2p=True)
        url = f'https://api.qiwi.com/partner/bill/v1/bills/{bill_id}/reject'
        async for response in self._requests.fast().fetch(
                url=url,
                method='POST',
                headers=headers
        ):
            return Bill.parse_obj(response.response_data)

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

        data = deepcopy(self._router.config.P2P_DATA)
        headers = self._auth_token(data.headers, p2p=True)
        url = self._p2p_router.build_url(
            "CHECK_P2P_BILL_STATUS",
            bill_id=bill_id
        )
        async for response in self._requests.fast().fetch(
                url=url,
                method='GET',
                headers=headers
        ):
            return Bill.parse_obj(response.response_data).status.value

    async def create_p2p_bill(
            self,
            amount: int,
            bill_id: Optional[str] = None,
            comment: Optional[str] = None,
            life_time: Optional[datetime] = None,
            theme_code: Optional[str] = None,
            pay_source_filter: Optional[List[str]] = None
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

        _life_time = api_helper.datetime_to_str_in_iso(
            constants.DEFAULT_BILL_TIME if not life_time else life_time
        )

        data = deepcopy(self._p2p_router.config.P2P_DATA)

        headers = self._auth_token(data.headers, p2p=True)

        payload = api_helper.set_data_p2p_create(
            wrapped_data=data,
            amount=amount,
            comment=comment,
            theme_code=theme_code,
            pay_source_filter=pay_source_filter,
            life_time=str(_life_time)
        )
        url = self._p2p_router.build_url(
            "CREATE_P2P_BILL",
            bill_id=bill_id
        )
        async for response in self._requests.fast().fetch(
                url=url,
                json=payload,
                headers=headers,
                method='PUT'
        ):
            return Bill.parse_obj(response.response_data).initialize(self)

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
            deepcopy(self._router.config.DEFAULT_QIWI_HEADERS)
        )
        if rows > 50:
            raise InvalidData('Можно получить не более 50 счетов')

        params = {
            'rows': rows,
            'statuses': 'READY_FOR_PAY'
        }
        async for response in self._requests.fast().fetch(
                url=self._router.build_url("GET_BILLS"),
                headers=headers,
                method='GET',
                params=params
        ):
            return api_helper.simple_multiply_parse(
                response.response_data.get("bills"), Bill
            )

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
        url = self._router.build_url(
            "REFUND_BILL",
            refund_id=refund_id,
            bill_id=bill_id
        )
        headers = self._auth_token(
            deepcopy(self._router.config.DEFAULT_QIWI_HEADERS), p2p=True
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=headers,
                method='PUT',
                json=json_bill_data if isinstance(
                    json_bill_data,
                    dict
                ) else json_bill_data.json()
        ):
            return RefundBill.parse_obj(response.response_data)

    async def create_p2p_keys(
            self,
            key_pair_name: str,
            server_notification_url: Optional[str] = None) -> P2PKeys:
        """
        Метод создает новые p2p ключи

        :param key_pair_name: Название пары токенов P2P (произвольная строка)
        :param server_notification_url: url для вебхуков, необязательный
         параметр
        """
        url = self._router.build_url("CREATE_P2P_KEYS")
        headers = self._auth_token(
            deepcopy(self._router.config.DEFAULT_QIWI_HEADERS), p2p=True
        )
        data = {
            'keysPairName': key_pair_name,
            'serverNotificationsUrl': server_notification_url
        }
        async for response in self._requests.fast().fetch(
                url=url,
                headers=headers,
                json=data
        ):
            return P2PKeys.parse_obj(response.response_data)
