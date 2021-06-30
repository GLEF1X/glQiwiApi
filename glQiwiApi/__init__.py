import sys

from .qiwi import QiwiWrapper, QiwiMaps
from .utils.api_helper import sync, async_as_sync
from .utils.errors import (
    InvalidData,
    NoUrlFound,
    RequestAuthError,
    RequestProxyError,
    NetworkError,
    InvalidCardNumber,
    RequestError,
    NoUpdatesToExecute,
    StateError,
    InvalidToken,
    InvalidCachePayload,
)
from .yoo_money import YooMoneyAPI

__version__ = "1.0.2"

__all__ = (
    "QiwiWrapper",
    "YooMoneyAPI",
    "QiwiMaps",
    "sync",
    "async_as_sync",
    # Exceptions
    "InvalidData",
    "NoUrlFound",
    "RequestAuthError",
    "RequestProxyError",
    "InvalidCardNumber",
    "InvalidToken",
    "RequestError",
    "NoUpdatesToExecute",
    "StateError",
    "NetworkError",
    "InvalidCachePayload",
)


class VersionError(Exception):
    """
    Ошибка возникает, если ваша версия python не поддерживается библиотекой

    """


if not sys.version_info[:2] >= (3, 7):
    raise VersionError(
        "Ваша версия python не поддерживается библиотекой glQiwiApi."
        "Минимальная версия для использования python 3.7"
    )
