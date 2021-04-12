import copy
from typing import Optional, Any

from glQiwiApi.types.basics import Attributes


class BillMixin(object):
    """
    Примесь, позволяющая проверять счет, не используя метод QiwiWrapper,
    добавляя метод check() объекту Bill
    """
    _w = None
    bill_id: Optional[str] = None

    def initialize(self, w: Any):
        self._w = copy.copy(w)
        return self

    async def check(self) -> bool:
        async with self._w:
            return (await self._w.check_p2p_bill_status(
                bill_id=self.bill_id
            )) == 'PAID'


class ToolsMixin(object):
    _parser = None

    async def __aenter__(self):
        """Создаем сессию, чтобы не пересоздавать её много раз"""
        self._parser.create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрываем сессию при выходе"""
        if self._parser.session:
            await self._parser.session.close()

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k == '_parser':
                v.session = None
            setattr(result, k, copy.deepcopy(v, memo))

        return result

    @property
    def parser(self):
        return self._parser


class SimpleCache(object):

    def __init__(self) -> None:
        self._cache: Optional[Attributes] = None

    def __del__(self) -> None:
        del self._cache

    def get(self) -> Optional[Attributes]:
        return self._cache

    def set(self, result: Any, kwargs: Any) -> None:
        data = kwargs.get('json') \
            if kwargs.get('json') is not None else kwargs.get('data')
        self._cache = Attributes(data, result)

    def validate(self, kwargs) -> bool:
        if isinstance(self._cache, Attributes):
            json = kwargs.get('json')
            data = kwargs.get('data')
            if isinstance(json, dict) or isinstance(data, dict):
                if data == self._cache.kwargs or json == self._cache.kwargs:
                    return True
        return False
