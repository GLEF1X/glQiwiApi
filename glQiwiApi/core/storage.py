import time
import typing

from glQiwiApi.core import BaseStorage
from glQiwiApi.core.constants import uncached
from glQiwiApi.types.basics import Cached, Attributes

MEMData = typing.TypeVar("MEMData", bound=typing.Dict[typing.Any, typing.Any])


class Storage(BaseStorage[MEMData]):
    """
    Deal with cache and data. Easy to use

    >>> storage = Storage(cache_time=5)
    >>> storage["hello_world"] = 5
    >>> print(storage["hello_world"])  # print 5

    """
    # Доступные критерии, по которым проходит валидацию кэш
    _validator_args = ('params', 'json', 'data', 'headers')

    __slots__ = ('data', '_cache_time')

    def __init__(self, *, cache_time: typing.Union[float, int]) -> None:
        """

        :param cache_time: Время кэширования в секундах
        """

        self.data: MEMData = dict()
        self._cache_time = cache_time

    def clear(self, key: typing.Optional[str] = None, *,
              force: bool = False) -> typing.Any:
        """
        Method to delete element from the cache by key,
        or if force passed on its clear all data from the cache

        :param key: by this key to delete an element in storage
        :param force: If this argument is passed as True,
         the date in the storage will be completely cleared.

        """
        if force:
            return self.data.clear()
        return self.data.pop(key)

    def __setitem__(self, key, value) -> None:
        return self.update_data(value, key)

    def __getitem__(self, item) -> typing.Any:
        try:
            obj = self.data[item]
            if not self._is_expire(obj["cached_in"], item):
                return obj["data"]
        except KeyError:
            pass

    def _is_contain_uncached(self, value: typing.Optional[typing.Any]) -> bool:
        if self._cache_time < 0.1:
            return True

        for coincidence in uncached:
            try:
                if value.startswith(coincidence) or coincidence in value:
                    return True
            except AttributeError:
                return False
        return False

    def convert_to_cache(
            self,
            result: typing.Any,
            kwargs: dict,
            status_code: typing.Union[str, int]
    ) -> Cached:
        """
        Method, which convert response of API to :class:`Cached`

        :param result: response data
        :param kwargs: key/value of request payload data
        :param status_code: status_code answer
        """
        value = kwargs.get("url")
        if not self._is_contain_uncached(value):
            return Cached(
                kwargs=Attributes.format(kwargs, self._validator_args),
                response_data=result,
                status_code=status_code,
                method=kwargs.get('method')
            )
        elif uncached[1] in value:
            self.clear(value, force=True)

    def update_data(self, obj_to_cache: typing.Any, key: typing.Any) -> None:
        """
        Метод, который добавляет результат запроса в кэш.

        >>> storage = Storage(cache_time=5)
        >>> storage.update_data(obj_to_cache="hello world", key="world")
        >>> storage["world"] = "hello_world"  # This approach is in priority and
                                              # the same as on the line of code above

        :param obj_to_cache: объект для кэширования
        :param key: ключ, по которому будет зарезервирован этот кэш
        """
        if not self._is_contain_uncached(obj_to_cache):
            self.data[key] = {
                "data": obj_to_cache,
                "cached_in": time.monotonic(),
            }

    @staticmethod
    def _check_get_request(cached: Cached, kwargs: dict) -> bool:
        """ Method to check cached get requests"""
        if cached.method == 'GET':
            if kwargs.get('headers') == cached.kwargs.headers:
                if kwargs.get('params') == cached.kwargs.params:
                    return True
        return False

    def _is_expire(self, cached_in: float, key: typing.Any) -> bool:
        """ Method to check live cache time, and if it expired return True """
        if time.monotonic() - cached_in > self._cache_time:
            self.clear(key)
            return True
        return False

    def _validate_other(self, cached: Cached, kwargs: dict) -> bool:
        keys = (key for key in self._validator_args if key != 'headers')
        for key in keys:
            if getattr(cached.kwargs, key) == kwargs.get(key, ''):
                return True
        return False

    def validate(self, kwargs: typing.Dict[str, typing.Any]) -> bool:
        """
        Метод, который по некоторым условиям
        проверяет актуальность кэша и в некоторых
        случая его чистит.

        :param kwargs:
        :return: boolean, прошел ли кэшированный запрос валидацию
        """
        # Если параметры и ссылка запроса совпадает
        cached = self[kwargs.get("url")]
        if isinstance(cached, Cached):
            # Проверяем запрос методом GET на кэш
            if self._check_get_request(cached, kwargs):
                return True
            elif self._validate_other(cached, kwargs):
                return True

        return False
