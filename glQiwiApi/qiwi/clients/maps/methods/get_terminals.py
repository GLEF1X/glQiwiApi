from typing import Any, ClassVar, Dict, List, Optional

from pydantic import Field

from glQiwiApi.core.abc.api_method import Request
from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.maps.types.polygon import Polygon
from glQiwiApi.qiwi.clients.maps.types.terminal import Terminal


class GetTerminals(QiwiAPIMethod[List[Terminal]]):
    url: ClassVar[str] = 'http://edge.qiwi.com/locator/v3/nearest/clusters?parameters'
    http_method: ClassVar[str] = 'GET'

    polygon: Polygon
    pop_if_inactive_x_mins: int = Field(..., alias='activeWithinMinutes')
    zoom: Optional[int] = None
    include_partners: Optional[bool] = Field(None, alias='withRefillWallet')
    partners_ids: Optional[List[Any]] = Field(None, alias='ttpIds')
    cache_terminals: Optional[bool] = Field(None, alias='cacheAllowed')
    card_terminals: Optional[bool] = Field(None, alias='cardAllowed')
    identification_types: Optional[int] = Field(None, alias='identificationTypes')
    terminal_groups: Optional[List[Any]] = Field(
        None,
        alias='ttpGroups',
    )

    def build_request(self, **url_format_kw: Any) -> 'Request':
        model_dict = self.dict(exclude_none=True, exclude_unset=True, by_alias=True)
        polygon = model_dict.pop('polygon')

        model_dict = _replace_bool_values_with_strings(model_dict)

        return Request(
            endpoint=self.url.format(**url_format_kw, **self._get_runtime_path_values()),
            http_method=self.http_method,
            params={**model_dict, **polygon},
        )


def _replace_bool_values_with_strings(d: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in d.items():
        if not isinstance(v, bool):
            continue

        d[k] = str(v)
    return d
