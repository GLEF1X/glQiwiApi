import sys

from .qiwi import QiwiWrapper, QiwiMaps  # NOQA
from .utils.basics import sync  # NOQA
from .utils.exceptions import *  # NOQA
from .yoo_money import YooMoneyAPI  # NOQA

__version__ = '0.2.19'

__all__ = (
        (
            'QiwiWrapper',
            'YooMoneyAPI',
            'QiwiMaps',
            'sync',
        ) + utils.exceptions.__all__  # NOQA
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
