import sys

from .qiwi import QiwiWrapper, QiwiMaps  # NOQA  # type: ignore
from .utils.basics import sync, async_as_sync  # NOQA  # type: ignore
from .utils.exceptions import *  # NOQA  # type: ignore
from .yoo_money import YooMoneyAPI  # NOQA  # type: ignore

__version__ = '1.0.2'

__all__ = (
        (
            'QiwiWrapper',
            'YooMoneyAPI',
            'QiwiMaps',
            'sync',
            'async_as_sync'
        ) + utils.exceptions.__all__  # NOQA  # type: ignore
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
