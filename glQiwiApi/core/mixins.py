import copy
from typing import Optional, Any


class BillMixin(object):
    """
    Примесь, позволяющая проверять счет, не используя метод QiwiWrapper,
    добавляя метод check() объекту Bill

    """
    _w = None
    bill_id: Optional[str] = None

    def initialize(self, wallet: Any):
        self._w = copy.copy(wallet)
        return self

    async def check(self) -> bool:
        async with self._w:
            return (await self._w.check_p2p_bill_status(
                bill_id=self.bill_id
            )) == 'PAID'


class ToolsMixin(object):
    """ Object: ToolsMixin """
    _requests = None

    async def __aenter__(self):
        """Создаем сессию, чтобы не пересоздавать её много раз"""
        self._requests.create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрываем сессию и очищаем кэш при выходе"""
        if self._requests.session:
            await self._requests.session.close()
            self._requests.clear_cache()

    def _get(self, item: Any) -> Any:
        try:
            return super().__getattribute__(item)
        except AttributeError:
            return None

    def __deepcopy__(self, memo) -> 'ToolsMixin':
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        dct = {slot: self._get(slot) for slot in self.__slots__ if
               self._get(slot) is not None}
        for k, value in dct.items():
            if k == '_parser':
                value.session = None
            setattr(result, k, copy.deepcopy(value, memo))

        return result
