import sys

from glQiwiApi.utils import exceptions
from .qiwi import QiwiWrapper, QiwiMaps  # NOQA
from .utils.basics import sync, to_datetime  # NOQA
from .utils.exceptions import *  # NOQA
from .yoo_money import YooMoneyAPI  # NOQA

__all__ = (
        (
            'QiwiWrapper',
            'YooMoneyAPI',
            'QiwiMaps',
            'RequestError',
            'to_datetime',
            'sync'
        ) + exceptions.__all__  # NOQA
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

__version__ = '0.2.13'
