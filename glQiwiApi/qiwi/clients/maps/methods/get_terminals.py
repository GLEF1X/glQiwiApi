from typing import List, ClassVar, Optional, Any

from pydantic import Field

from glQiwiApi.qiwi.base import QiwiAPIMethod
from glQiwiApi.qiwi.clients.maps.types.polygon import Polygon
from glQiwiApi.qiwi.clients.maps.types.terminal import Terminal


class GetTerminals(QiwiAPIMethod[List[Terminal]]):
    url: ClassVar[str] = "http://edge.qiwi.com/locator/v3/nearest/clusters?parameters"
    http_method: ClassVar[str] = "GET"

    polygon: Polygon
    pop_if_inactive_x_mins: int = Field(..., alias="activeWithinMinutes")
    zoom: Optional[int] = None
    include_partners: Optional[bool] = Field(None, alias="withRefillWallet")
    partners_ids: Optional[List[Any]] = Field(None, alias="ttpIds")
    cache_terminals: Optional[bool] = Field(None, alias="cacheAllowed")
    card_terminals: Optional[bool] = Field(None, alias="cardAllowed")
    identification_types: Optional[int] = Field(None, alias="identificationTypes")
    terminal_groups: Optional[List[Any]] = Field(None, alias="ttpGroups")
