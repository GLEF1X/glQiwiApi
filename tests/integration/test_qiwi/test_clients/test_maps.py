from typing import Any, AsyncIterator, Dict

import pytest

from glQiwiApi import QiwiMaps
from glQiwiApi.qiwi.clients.maps.types.polygon import Polygon
from glQiwiApi.qiwi.clients.maps.types.terminal import Terminal
from glQiwiApi.qiwi.clients.wallet.types import Partner

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="data")
def maps_data() -> AsyncIterator[Dict[str, Any]]:
    polygon = Polygon(latNW=55.690881, lngNW=37.386282, latSE=55.580184, lngSE=37.826078)
    yield {"polygon": polygon, "zoom": 12, "cache_terminals": True}
    del polygon


@pytest.fixture(name="maps")
async def maps_fixture() -> AsyncIterator[QiwiMaps]:
    """:class:`QiwiMaps` fixture"""
    async with QiwiMaps() as maps:
        yield maps


async def test_terminals(maps: QiwiMaps, data: Dict[str, Any]) -> None:
    result = await maps.terminals(**data, include_partners=True)
    assert all(isinstance(t, Terminal) for t in result)


async def test_partners(maps: QiwiMaps) -> None:
    result = await maps.partners()
    assert all(isinstance(p, Partner) for p in result)
