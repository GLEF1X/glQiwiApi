import pytest
from glQiwiApi import types, QiwiMaps

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="data")
def maps_data():
    polygon = types.Polygon((55.690881, 37.386282), (55.580184, 37.826078))
    yield {
        "polygon": polygon,
        "zoom": 12,
        "cache_terminals": True
    }


@pytest.fixture(name="maps")
async def maps_fixture():
    _maps = QiwiMaps()
    yield _maps
    await _maps.close()


async def test_terminals(maps: QiwiMaps, data: dict):
    async with maps:
        result = await maps.terminals(**data)
    assert all(isinstance(t, types.Terminal) for t in result)


async def test_partners(maps: QiwiMaps):
    async with maps:
        result = await maps.partners()
    assert all(isinstance(p, types.Partner) for p in result)
