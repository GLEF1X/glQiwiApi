from __future__ import annotations

import typing

from glQiwiApi import types
from glQiwiApi.core import RequestService
from glQiwiApi.core.abc.wrapper import Wrapper
from glQiwiApi.core.constants import NO_CACHING
from glQiwiApi.core.mixins import ContextInstanceMixin, DataMixin
from glQiwiApi.core.session.holder import AbstractSessionHolder
from glQiwiApi.utils.payload import parse_iterable_to_list_of_objects, filter_none


class QiwiMaps(Wrapper, DataMixin, ContextInstanceMixin["QiwiMaps"]):
    """
    QIWI Terminal Maps API allows you to locate
    QIWI terminals on the territory of the Russian Federation

    """

    def __init__(self, cache_time: int = NO_CACHING,
                 session_holder: typing.Optional[AbstractSessionHolder[typing.Any]] = None) -> None:
        self._request_service = RequestService(cache_time=cache_time, session_holder=session_holder)

    def get_request_service(self) -> RequestService:
        return self._request_service

    async def terminals(
            self,
            polygon: types.Polygon,
            zoom: typing.Optional[int] = None,
            pop_if_inactive_x_mins: int = 30,
            include_partners: typing.Optional[bool] = None,
            partners_ids: typing.Optional[typing.List[typing.Any]] = None,
            cache_terminals: typing.Optional[bool] = None,
            card_terminals: typing.Optional[bool] = None,
            identification_types: typing.Optional[int] = None,
            terminal_groups: typing.Optional[typing.List[typing.Any]] = None,
    ) -> typing.List[types.Terminal]:
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
        params = filter_none(
            {
                **polygon.dict,
                "zoom": zoom,
                "activeWithinMinutes": pop_if_inactive_x_mins,
                "withRefillWallet": include_partners,
                "ttpIds": partners_ids,
                "cacheAllowed": cache_terminals,
                "cardAllowed": card_terminals,
                "identificationTypes": identification_types,
                "ttpGroups": terminal_groups,
            }
        )
        url = "http://edge.qiwi.com/locator/v3/nearest/clusters?parameters"
        response = await self._request_service.raw_request(url, "GET", params=params)
        return parse_iterable_to_list_of_objects(
            typing.cast(typing.List[typing.Any], response), types.Terminal
        )

    async def partners(self) -> typing.List[types.Partner]:
        """
        Get terminal partners for ttpGroups
        :return: list of TTPGroups
        """
        url = "http://edge.qiwi.com/locator/v3/ttp-groups"
        response = await self._request_service.raw_request(
            url, "GET", headers={"Content-type": "text/json"}
        )
        return parse_iterable_to_list_of_objects(
            typing.cast(typing.List[typing.Any], response), types.Partner
        )
