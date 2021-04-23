import typing

import glQiwiApi.utils.basics as api_helper
from glQiwiApi import types
from glQiwiApi.core import RequestManager, ToolsMixin
from glQiwiApi.types.basics import DEFAULT_CACHE_TIME


class QiwiMaps(ToolsMixin):
    """
    API Карты терминалов QIWI позволяет установить местонахождение
    терминалов QIWI на территории РФ

    """

    def __init__(
            self,
            without_context: bool = False,
            cache_time: int = DEFAULT_CACHE_TIME
    ) -> None:
        self._requests = RequestManager(
            without_context=without_context,
            cache_time=cache_time
        )

    async def terminals(
            self,
            polygon: types.Polygon,
            zoom: int = None,
            pop_if_inactive_x_mins: int = 30,
            include_partners: bool = None,
            partners_ids: list = None,
            cache_terminals: bool = None,
            card_terminals: bool = None,
            identification_types: int = None,
            terminal_groups: list = None,
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
        params = self._requests.filter_dict(
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
        async for response in self._requests.fast().fetch(
                url=url,
                method='GET',
                params=params
        ):
            return api_helper.multiply_objects_parse(
                lst_of_objects=response.response_data,
                model=types.Terminal
            )

    async def partners(self) -> typing.List[types.Partner]:
        """
        Get terminal partners for ttpGroups
        :return: list of TTPGroups
        """
        async for response in self._requests.fast().fetch(
                url='http://edge.qiwi.com/locator/v3/ttp-groups',
                method='GET',
                headers={"Content-type": "text/json"}
        ):
            return api_helper.multiply_objects_parse(
                lst_of_objects=response.response_data,
                model=types.Partner
            )
