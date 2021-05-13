import uuid
from copy import deepcopy
from typing import Any, Optional, Union, List, MutableMapping

from glQiwiApi.types import Commission, CrossRate, Sum, PaymentMethod, \
    FreePaymentDetailsFields, PaymentInfo
from glQiwiApi.utils.exceptions import InvalidCardNumber
from glQiwiApi.core.abstracts import AbstractRouter
from glQiwiApi.utils import basics as api_helper


class QiwiPaymentsMixin:
    """Provides payment QIWI API"""

    def __init__(self, requests_manager: Any, router: AbstractRouter):
        self._requests = requests_manager
        self._router: AbstractRouter = router

    def _auth_token(
            self,
            headers: MutableMapping,
            p2p: bool = False
    ) -> MutableMapping:
        ...

    async def to_wallet(
            self,
            to_number: str,
            trans_sum: Union[str, float, int],
            currency: str = '643',
            comment: str = '+comment+') -> Optional[str]:
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
            data=deepcopy(self._router.config.QIWI_TO_WALLET),
            to_number=to_number,
            trans_sum=trans_sum,
            currency=currency,
            comment=comment
        )
        data.headers = self._auth_token(
            headers=data.headers
        )
        async for response in self._requests.fast().fetch(
                url=self._router.build_url("TO_WALLET"),
                json=data.json,
                headers=data.headers
        ):
            return response.response_data['transaction']['id']

    async def to_card(
            self,
            trans_sum: Union[float, int],
            to_card: str
    ) -> Optional[str]:
        """
        Метод для отправки средств на карту.
        Более подробная документация:
        https://developer.qiwi.com/ru/qiwi-wallet-personal/#cards

        :param trans_sum: сумма перевода
        :param to_card: номер карты получателя
        :return:
        """
        data = api_helper.parse_card_data(
            default_data=self._router.config.QIWI_TO_CARD,
            to_card=to_card,
            trans_sum=trans_sum,
            auth_maker=self._auth_token
        )
        privat_card_id = await self._detect_card_number(card_number=to_card)
        async for response in self._requests.fast().fetch(
                url=self._router.build_url(
                    "TO_CARD", privat_card_id=privat_card_id
                ),
                headers=data.headers,
                json=data.json,
                get_json=True
        ):
            return response.response_data.get('id')

    async def _detect_card_number(self, card_number: str) -> str:
        """
        Метод для получения идентификатора карты

        https://developer.qiwi.com/ru/qiwi-wallet-personal/?python#cards
        """
        headers = deepcopy(self._router.config.DEFAULT_QIWI_HEADERS)
        headers.update(
            {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )
        async for response in self._requests.fetch(
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
        payload, special_code = api_helper.parse_commission_request_payload(
            default_data=self._router.config.COMMISSION_DATA,
            auth_maker=self._auth_token,
            to_account=to_account,
            pay_sum=pay_sum
        )
        if not isinstance(special_code, str):
            special_code = await self._detect_card_number(
                card_number=to_account
            )
        url = self._router.build_url("COMMISSION", special_code=special_code)
        async for response in self._requests.fast().fetch(
                url=url,
                headers=payload.headers,
                json=payload.json
        ):
            return Commission.parse_obj(response.response_data)

    async def get_cross_rates(self) -> List[CrossRate]:
        """
        Метод возвращает текущие курсы и кросс-курсы валют КИВИ Банка.

        """
        url = self._router.build_url("GET_CROSS_RATES")
        async for response in self._requests.fast().fetch(
                url=url,
                method='GET'
        ):
            return api_helper.simple_multiply_parse(
                lst_of_objects=response.response_data.get("result"),
                model=CrossRate
            )

    async def payment_by_payment_details(
            self,
            payment_sum: Sum,
            payment_method: PaymentMethod,
            fields: FreePaymentDetailsFields,
            payment_id: Optional[str] = None
    ) -> PaymentInfo:
        """
        Оплата услуг коммерческих организаций по их банковским реквизитам.

        :param payment_id: id платежа, если не передается, используется
         uuid4
        :param payment_sum: обьект Sum, в котором указывается сумма платежа
        :param payment_method: метод платежа
        :param fields: Набор реквизитов платежа
        """
        url = self._router.build_url("SPECIAL_PAYMENT")
        headers = deepcopy(self._router.config.DEFAULT_QIWI_HEADERS)
        payload = {
            "id": payment_id if isinstance(payment_id, str) else str(
                uuid.uuid4()
            ),
            "sum": payment_sum.dict(),
            "paymentMethod": payment_method.dict(),
            "fields": fields.dict()
        }
        async for response in self._requests.fast().fetch(
                url=url,
                json=payload,
                headers=headers
        ):
            return PaymentInfo.parse_obj(response.response_data)
