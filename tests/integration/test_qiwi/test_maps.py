
from typing import Any, Dict

import pytest

from glQiwiApi import QiwiMaps
from glQiwiApi.qiwi.clients.maps.types.polygon import Polygon
from glQiwiApi.qiwi.clients.maps.types.terminal import Terminal
from glQiwiApi.qiwi.clients.wallet.types import Partner

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="data")
def maps_data():
    polygon = Polygon((55.690881, 37.386282), (55.580184, 37.826078))
    yield {"polygon": polygon, "zoom": 12, "cache_terminals": True}
    del polygon


@pytest.fixture(name="maps")
async def maps_fixture():
    """:class:`QiwiMaps` fixture"""
    _maps = QiwiMaps()
    yield _maps
    await _maps.close()


async def test_terminals(maps: QiwiMaps, data: Dict[str, Any]) -> None:
    result = await maps.terminals(**data)
    assert all(isinstance(t, Terminal) for t in result)


async def test_partners(maps: QiwiMaps) -> None:
    result = await maps.partners()
    assert all(isinstance(p, Partner) for p in result)
