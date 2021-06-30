import pathlib

import pytest

pytestmark = pytest.mark.asyncio


def _safe_delete_directory(path_to_dir: pathlib.Path):
    for file in path_to_dir.iterdir():
        file.unlink()
    path_to_dir.rmdir()


@pytest.fixture(name="path_to_dir", scope="session")
def receipt_file():
    """Create temporary directory fixture"""
    from .types.dataset import TEMP_DIRECTORY_NAME

    cur_dir = pathlib.Path.cwd()
    path_to_dir = cur_dir / TEMP_DIRECTORY_NAME
    path_to_dir.mkdir(exist_ok=True)
    yield path_to_dir
    _safe_delete_directory(path_to_dir)


@pytest.fixture(name="credentials")
def credentials():
    from .types.dataset import API_DATA

    """ credentials fixture """
    yield API_DATA


@pytest.fixture(name="yoo_credentials")
def credentials_fixture():
    from .types.dataset import YOO_MONEY_DATA

    """ Юмани credentials fixture """
    yield YOO_MONEY_DATA
