import aiohttp
import pytest

from glQiwiApi import QiwiWrapper, InvalidData
from glQiwiApi.core import RequestManager
from glQiwiApi.core.web_hooks.dispatcher import Dispatcher
from glQiwiApi.qiwi.settings import QiwiRouter, QiwiKassaRouter

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock, patch  # type: ignore

pytestmark = pytest.mark.asyncio


class TestAiohttpSession:

    async def test_create_api(self):
        from tests.types.dataset import API_DATA
        api = QiwiWrapper(**API_DATA)

        # initially session is None,
        # it's done  to save performance and
        # it creates new session when you make a request (API method call)
        assert api.session is None

        # such a session is created under the hood(when you call API method)
        api._requests.create_session()

        # And now it's aiohttp.ClientSession instance
        assert isinstance(api.session, aiohttp.ClientSession)

        assert isinstance(api._router, QiwiRouter)
        assert isinstance(api._requests, RequestManager)
        assert isinstance(api._p2p_router, QiwiKassaRouter)
        assert isinstance(api.dispatcher, Dispatcher)

        # close session =)
        await api.close()

    async def test_create_api_with_wrong_data(self):
        from tests.types.dataset import WRONG_API_DATA
        with pytest.raises(InvalidData):
            QiwiWrapper(**WRONG_API_DATA)

    async def test_close_session(self):
        from tests.types.dataset import API_DATA
        api = QiwiWrapper(**API_DATA)

        api._requests.create_session()

        aiohttp_session = api.session

        with patch("aiohttp.ClientSession.close",
                   new=CoroutineMock()) as mocked_close:
            await aiohttp_session.close()
            mocked_close.assert_called_once()

        await api.close()
