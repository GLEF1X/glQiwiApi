import datetime
import uuid
from typing import Dict

import aiohttp
import pytest

from glQiwiApi import QiwiWrapper, sync
from glQiwiApi import types


@pytest.fixture(name="api")
def sync_api_fixture(credentials: Dict[str, str]):
    _wrapper = QiwiWrapper(**credentials, without_context=True)
    yield _wrapper


def test_sync_get_balance(api: QiwiWrapper):
    result = sync(api.get_balance)
    assert isinstance(result, types.Sum)


@pytest.mark.parametrize("params", [
    {"amount": 1},
    {"amount": 1, "comment": "test_comment"},
    {
        "amount": 1,
        "comment": "test_comment",
        "life_time": datetime.datetime.now() + datetime.timedelta(hours=5)
    },
    {
        "amount": 1,
        "comment": "test_comment",
        "life_time": datetime.datetime.now() + datetime.timedelta(hours=5),
        "bill_id": str(uuid.uuid4())
    }
])
def test_sync_create_p2p_bill(api: QiwiWrapper, params: dict):
    result = sync(api.create_p2p_bill, **params)
    assert isinstance(result, types.Bill)


class SyncApiSessionTest:

    @pytest.mark.last
    def test_is_session_closing(self, api: QiwiWrapper):
        # Send request to API
        sync(api.get_balance)

        api_session = api.session

        assert isinstance(api_session, aiohttp.ClientSession)

        # Send new request to API

        sync(api.get_balance)

        new_session = api.session

        assert api_session != new_session
