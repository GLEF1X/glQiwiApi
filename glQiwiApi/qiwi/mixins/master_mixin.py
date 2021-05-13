from copy import deepcopy
from typing import Optional, Any, MutableMapping

from glQiwiApi.core.abstracts import AbstractRouter
from glQiwiApi.types import PaymentInfo, OrderDetails
from glQiwiApi.utils import basics as api_helper


class QiwiMasterMixin:
    """Mixin, which implements QIWI master API logic"""

    def __init__(self, router: AbstractRouter, request_manager: Any):
        self._router = router
        self._requests = request_manager

    def _auth_token(
            self,
            headers: MutableMapping,
            p2p: bool = False
    ) -> MutableMapping:
        ...

    @property
    def stripped_number(self) -> str:
        return ""

    async def buy_qiwi_master(self) -> PaymentInfo:
        """
        Метод для покупки пакета QIWI Мастер

        Для вызова методов API вам потребуется токен API QIWI Wallet
        с разрешениями на следующие действия:

        1. Управление виртуальными картами,
        2. Запрос информации о профиле кошелька,
        3. Просмотр истории платежей,
        4. Проведение платежей без SMS.

        Эти права вы можете выбрать при создании нового апи токена,
        чтобы пользоваться апи QIWI Master
        """
        url = self._router.build_url("BUY_QIWI_MASTER")
        payload = api_helper.qiwi_master_data(self.stripped_number,
                                              self._router.config.QIWI_MASTER)
        async for response in self._requests.fast().fetch(
                url=url,
                json=payload,
                method='POST',
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                ))
        ):
            return PaymentInfo.parse_obj(response.response_data)

    async def __pre_qiwi_master_request(
            self,
            card_alias: str = 'qvc-cpa'
    ) -> OrderDetails:
        """
        Метод для выпуска виртуальной карты QIWI Мастер

        :param card_alias: Тип карты
        :return: OrderDetails
        """
        url = self._router.build_url(
            "PRE_QIWI_REQUEST",
            stripped_number=self.stripped_number
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                json={"cardAlias": card_alias},
                method='POST'
        ):
            return OrderDetails.parse_obj(response.response_data)

    async def _confirm_qiwi_master_request(
            self,
            card_alias: str = 'qvc-cpa'
    ) -> OrderDetails:
        """
        Подтверждение заказа выпуска карты

        :param card_alias: Тип карты
        :return: OrderDetails
        """
        details = await self.__pre_qiwi_master_request(card_alias)
        url = self._router.build_url(
            "_CONFIRM_QIWI_MASTER",
            stripped_number=self.stripped_number,
            order_id=details.order_id
        )
        async for response in self._requests.fast().fetch(
                url=url,
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                method='PUT'
        ):
            return OrderDetails.parse_obj(response.response_data)

    async def __buy_new_qiwi_card(
            self,
            **kwargs
    ) -> Optional[OrderDetails]:
        """
        Покупка карты, если она платная

        :param kwargs:
        :return: OrderDetails
        """
        kwargs.update(data=self._router.config.QIWI_MASTER)
        url, payload = api_helper.new_card_data(**kwargs)
        async for response in self._requests.fast().fetch(
                url=url,
                json=payload,
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                ))
        ):
            return OrderDetails.parse_obj(response.response_data)

    async def issue_qiwi_master_card(
            self,
            card_alias: str = 'qvc-cpa'
    ) -> Optional[OrderDetails]:
        """
        Выпуск новой карты, используя Qiwi Master API

        При выпуске карты производиться 3, а возможно 3 запроса,
        а именно по такой схеме:
            - __pre_qiwi_master_request - данный метод создает заявку
            - _confirm_qiwi_master_request - подтверждает выпуск карты
            - __buy_new_qiwi_card - покупает новую карту,
              если такая карта не бесплатна


        Подробная документация:

        https://developer.qiwi.com/ru/qiwi-wallet-personal/#qiwi-master-issue-card

        :param card_alias: Тип карты
        :return: OrderDetails
        """
        pre_response = await self._confirm_qiwi_master_request(card_alias)
        if pre_response.status == 'COMPLETED':
            return pre_response
        return await self.__buy_new_qiwi_card(
            ph_number=self.stripped_number,
            order_id=pre_response.order_id
        )

    async def _cards_qiwi_master(self):
        """
        Метод для получение списка всех ваших карт QIWI Мастер

        """
        url = self._router.build_url("CARDS_QIWI_MASTER")
        async for response in self._requests.fast().fetch(
                url=url,
                headers=self._auth_token(deepcopy(
                    self._router.config.DEFAULT_QIWI_HEADERS
                )),
                method='GET'
        ):
            return response
