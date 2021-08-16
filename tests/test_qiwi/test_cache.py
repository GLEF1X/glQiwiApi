import asyncio
import datetime
from typing import Dict

import pytest

from glQiwiApi import QiwiWrapper

pytestmark = pytest.mark.asyncio

CACHE_TIME = 5


@pytest.fixture(name="api")
async def api_fixture(credentials: Dict[str, str]):
    """Api fixture"""
    _wrapper = QiwiWrapper(**credentials, cache_time=CACHE_TIME)  # type: ignore
    yield _wrapper
    await _wrapper.close()


class TestCache:
    @pytest.mark.parametrize(
        "payload",
        [
            {"rows": 50},
            {"rows": 50, "operation": "IN"},
            {
                "rows": 50,
                "operation": "IN",
                "start_date": datetime.datetime.now() - datetime.timedelta(days=50),
                "end_date": datetime.datetime.now(),
            },
        ],
    )
    async def test_query_caching(self, api: QiwiWrapper, payload: dict):
        async with api:
            first_response = await api.transactions(**payload)
            second_response = await asyncio.wait_for(
                api.transactions(**payload),
                0.07  # We are waiting for task for 7 milliseconds,
                # because if the query has cached, it will just take
                # it from storage and API will take less time than query,
                # so there if query wont work we will see TimeoutError
            )

        assert first_response == second_response

    @pytest.mark.parametrize(
        "payload1,payload2",
        [
            ({"rows": 50}, {"rows": 40}),
            ({"rows": 50, "operation": "IN"}, {"rows": 50, "operation": "OUT"}),
        ],
    )
    async def test_uncached(self, api: QiwiWrapper, payload1: dict, payload2: dict):
        async with api:
            first_response = await api.transactions(**payload1)
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(api.transactions(**payload2), 0.07)
            second_uncached_response = await api.transactions(**payload2)
        assert first_response != second_uncached_response

    @pytest.mark.parametrize(
        "payload",
        [
            {"rows": 50},
            {"rows": 50, "operation": "IN"},
            {
                "rows": 50,
                "operation": "IN",
                "start_date": datetime.datetime.now() - datetime.timedelta(days=50),
                "end_date": datetime.datetime.now(),
            },
        ],
    )
    async def test_response_cache_time(self, api: QiwiWrapper, payload: dict):
        async with api:
            await api.transactions(**payload)
            await asyncio.sleep(CACHE_TIME + 1)
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(api.transactions(**payload), 0.07)
