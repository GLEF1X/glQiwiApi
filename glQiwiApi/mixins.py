import copy
import itertools as it
from typing import Optional, Any


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
        """Закрываем сессию и очищаем кэш при выходе"""
        if self._parser.session:
            await self._parser.session.close()
            self._parser.clear_cache()

    def __deepcopy__(self, memo) -> 'ToolsMixin':
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        values = [getattr(self, slot) for slot in self.__slots__]
        items = it.zip_longest(self.__slots__, values)
        for k, v in items:
            if k == '_parser':
                v.session = None
            setattr(result, k, copy.deepcopy(v, memo))

        return result

    @property
    def parser(self):
        return self._parser
