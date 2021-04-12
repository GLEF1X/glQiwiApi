import sys

from glQiwiApi.qiwi import QiwiWrapper
from glQiwiApi.utils.exceptions import RequestError, VersionError
from glQiwiApi.yoo_money import YooMoneyAPI

__all__ = [
    'QiwiWrapper',
    'YooMoneyAPI',
    'RequestError'
]

if not sys.version_info[:2] >= (3, 7):
    raise VersionError(
        "Ваша версия python не поддерживается библиотекой glQiwiApi."
        "Минимальная версия для использования python 3.7"
    )

__version__ = '0.2.12'
