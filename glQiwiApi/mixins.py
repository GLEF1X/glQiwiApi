import copy
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
            return (await self._w.check_p2p_bill_status(bill_id=self.bill_id)) == 'PAID'


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
