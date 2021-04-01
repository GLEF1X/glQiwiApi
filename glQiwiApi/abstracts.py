import abc
import asyncio
import unittest


class AbstractPaymentWrapper(abc.ABC):
    @abc.abstractmethod
    async def get_balance(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def _auth_token(self, *args, **kwargs) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def to_card(self, *args, **kwargs) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def to_wallet(self, *args, **kwargs) -> None:
        raise NotImplementedError()


class AioTestCase(unittest.TestCase):

    # noinspection PyPep8Naming
    def __init__(self, methodName='runTest', loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self._function_cache = {}
        super(AioTestCase, self).__init__(methodName=methodName)

    def coroutine_function_decorator(self, func):
        def wrapper(*args, **kw):
            return self.loop.run_until_complete(func(*args, **kw))

        return wrapper

    def __getattribute__(self, item):
        attr = object.__getattribute__(self, item)
        if asyncio.iscoroutinefunction(attr):
            if item not in self._function_cache:
                self._function_cache[item] = self.coroutine_function_decorator(attr)
            return self._function_cache[item]
        return attr
