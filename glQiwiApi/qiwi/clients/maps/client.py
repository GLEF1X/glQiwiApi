import typing

from glQiwiApi.core.abc.base_api_client import BaseAPIClient, RequestServiceFactoryType
from glQiwiApi.core.request_service import RequestService, RequestServiceProto
from glQiwiApi.core.session import AiohttpSessionHolder
from glQiwiApi.qiwi.clients.maps.methods.get_partners import GetPartners
from glQiwiApi.qiwi.clients.maps.methods.get_terminals import GetTerminals
from glQiwiApi.qiwi.clients.maps.types.polygon import Polygon
from glQiwiApi.qiwi.clients.maps.types.terminal import Terminal
from glQiwiApi.qiwi.clients.wallet.types import Partner


class QiwiMaps(BaseAPIClient):
    """
    QIWI Terminal Maps API allows you to locate
    QIWI terminals on the territory of the Russian Federation

    """

    def __init__(
        self,
        request_service_factory: typing.Optional[RequestServiceFactoryType] = None,
    ) -> None:
        super().__init__(request_service_factory)

    async def _create_request_service(self) -> RequestServiceProto:
        return RequestService(
            session_holder=AiohttpSessionHolder(
                headers={
                    'Content-type': 'application/json',
                    'Accept': 'application/json',
                }
            )
        )

    async def terminals(
        self,
        polygon: Polygon,
        zoom: typing.Optional[int] = None,
        pop_if_inactive_x_mins: int = 30,
        include_partners: typing.Optional[bool] = None,
        partners_ids: typing.Optional[typing.List[typing.Any]] = None,
        cache_terminals: typing.Optional[bool] = None,
        card_terminals: typing.Optional[bool] = None,
        identification_types: typing.Optional[int] = None,
        terminal_groups: typing.Optional[typing.List[typing.Any]] = None,
    ) -> typing.List[Terminal]:
        """
        Get map of terminals sent for passed polygon with additional params

        :param polygon: glQiwiApi.types.Polygon object
        :param zoom:
         https://tech.yandex.ru/maps/doc/staticapi/1.x/dg/concepts/map_scale-docpage/
        :param pop_if_inactive_x_mins: do not show if terminal
         was inactive for X minutes default 0.5 hours
        :param include_partners: result will include/exclude partner terminals
        :param partners_ids: Not fixed IDS array look at docs
        :param cache_terminals: result will include or exclude
         cache-acceptable terminals
        :param card_terminals: result will include or
         exclude card-acceptable terminals
        :param identification_types: `0` - not identified, `1` -
         partly identified, `2` - fully identified
        :param terminal_groups: look at QiwiMaps.partners
        :return: list of Terminal instances
        """
        return await self._request_service.execute_api_method(
            GetTerminals(
                polygon=polygon,
                zoom=zoom,
                pop_if_inactive_x_mins=pop_if_inactive_x_mins,
                include_partners=include_partners,
                partners_ids=partners_ids,
                cache_terminals=cache_terminals,
                card_terminals=card_terminals,
                identification_types=identification_types,
                terminal_groups=terminal_groups,
            )
        )

    async def partners(self) -> typing.List[Partner]:
        """
        Get terminal partners for ttpGroups
        :return: list of TTPGroups
        """
        return await self._request_service.execute_api_method(GetPartners())
