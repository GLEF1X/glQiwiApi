import pytest

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="credentials")
def credentials():
    from .types.dataset import API_DATA

    """ credentials fixture """
    yield API_DATA


@pytest.fixture(name="yoo_credentials")
def credentials_fixture():
    from .types.dataset import YOO_MONEY_DATA

    yield YOO_MONEY_DATA
