import time
import typing

import aiohttp

from glQiwiApi.core import BaseStorage
from glQiwiApi.types.basics import Cached, Attributes
from glQiwiApi.utils.exceptions import InvalidData

MemData = typing.TypeVar(
    'MemData', bound=typing.Optional[
        typing.Dict[
            str,
            typing.Dict[
                str, typing.Any
            ]
        ]
    ]
)

uncached = (
    'https://api.qiwi.com/partner/bill',
    '/sinap/api/v2/terms/'
)


class Storage(BaseStorage):
    """
    Класс, позволяющий кэшировать результаты запросов

    """
    # Доступные критерии, по которым проходит валидацию кэш
    available = ('params', 'json', 'data', 'headers')

    __slots__ = ('data', '_cache_time', '_default_key')

    def __init__(
            self,
            cache_time: typing.Union[float, int],
            default_key: typing.Optional[str] = None
    ) -> None:
        """

        :param cache_time: Время кэширования в секундах
        :param default_key: дефолтный ключ, по которому будет доставаться кэш
        """
        if isinstance(cache_time, (int, float)):
            if cache_time > 60 or cache_time < 0:
                raise InvalidData(
                    "Время кэширования должно быть в пределах"
                    " от 0 до 60 секунд"
                )

        self.data: MemData = {}
        self._cache_time = cache_time
        self.__initialize_default_key(default_key)

    def __initialize_default_key(self, key: str) -> None:
        """ Initialize default_key attribute """
        self._default_key = key
        if not isinstance(key, str):
            self._default_key = "url"
        self.data.update({
            self._default_key: {}
        })

    def get_current(self, key: typing.Any) -> typing.Any:
        """ Method to get element by key from data """
        try:
            obj = self.data.get(self._default_key).get(key)
            return obj if not self._is_expire(obj) else None
        except AttributeError:
            return None

    def clear(self, key: typing.Optional[str] = None,
              force: bool = False) -> typing.Any:
        """
        Method to delete element from the cache by key,
        or if force passed on its clear all data from the cache

        """
        if force:
            return self.data.clear()
        return self.data[self._default_key].pop(key)

    def __setitem__(self, key, value) -> None:
        self.data[self._default_key][key] = value

    def __getitem__(self, item) -> typing.Union[
        Cached, aiohttp.ClientSession, None
    ]:
        try:
            return self.data[self._default_key][item]
        except KeyError:
            return None

    def _is_contain_uncached(self, value: str) -> bool:
        if self._cache_time < 0.1:
            return True

        for coincidence in uncached:
            try:
                if value.startswith(coincidence) or coincidence in value:
                    return True
            except AttributeError:
                return False
        return False

    def initialize_response_to_resolve(
            self,
            result: typing.Any,
            kwargs: dict,
            status_code: typing.Union[str, int]
    ) -> Cached:
        value = kwargs.get(self._default_key)
        if not self._is_contain_uncached(value):
            return Cached(
                kwargs=Attributes.format(kwargs, self.available),
                response_data=result,
                key=self._default_key,
                status_code=status_code,
                method=kwargs.get('method'),
                cache_to=value
            )
        elif uncached[1] in value:
            self.clear(value, True)

    def update_data(self, obj_to_cache: typing.Any, key: typing.Any) -> None:
        """
        Метод, который добавляет результат запроса в кэш

        :param obj_to_cache: объект для кэширования
        :param key: ключ, по которому будет зарезервирован этот кэш

        """
        if isinstance(obj_to_cache, Cached):
            key = obj_to_cache.cache_to
        else:
            try:
                setattr(obj_to_cache, 'cached_in', time.monotonic())
                setattr(obj_to_cache, 'cache_to', key)
            except AttributeError:
                pass
        if not self._is_contain_uncached(obj_to_cache):
            self.data[self._default_key][key] = obj_to_cache

    @staticmethod
    def _check_get_request(cached: Cached, kwargs: dict) -> bool:
        """ Method to check cached get requests"""
        if cached.method == 'GET':
            if kwargs.get('headers') == cached.kwargs.headers:
                if kwargs.get('params') == cached.kwargs.params:
                    return True
        return False

    def _is_expire(self, cached: typing.Any) -> bool:
        """ Method to check live cache time, and if it expired return True """
        if time.monotonic() - cached.cached_in > self._cache_time:
            self.clear(cached.cache_to)
            return True

    def _validate_other(self, cached: Cached, kwargs: dict) -> bool:
        keys = (key for key in self.available if key != 'headers')
        for key in keys:
            if getattr(cached.kwargs, key) == kwargs.get(key, ''):
                return True

    def validate(self, kwargs: typing.Dict[str, typing.Any]) -> bool:
        """
        Метод, который по некоторым условиям
        проверяет актуальность кэша и в некоторых
        случая его чистит.

        :param kwargs:
        :return: boolean, прошел ли кэшированный запрос валидацию
        """
        # Если параметры и ссылка запроса совпадает
        cached = self.get_current(kwargs.get(self._default_key))
        if isinstance(cached, Cached):
            if self._is_expire(cached):
                return False

            # Проверяем запрос методом GET на кэш
            if self._check_get_request(cached, kwargs):
                return True

            elif self._validate_other(cached, kwargs):
                return True

        return False
