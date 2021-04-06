import abc
import asyncio
import unittest
from typing import AsyncGenerator


class AbstractPaymentWrapper(abc.ABC):
    @abc.abstractmethod
    async def transactions(self, *args, **kwargs) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def transaction_info(self, *args, **kwargs) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def get_balance(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def account_info(self, *args, **kwargs) -> None:
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


class AbstractParser(abc.ABC):

    @abc.abstractmethod
    async def _request(self, *args, **kwargs) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    async def fetch(self, *args, **kwargs) -> AsyncGenerator:
        raise NotImplementedError()

    async def raise_exception(self, *args, **kwargs) -> None:
        """Метод для обработки исключений и лучшего логирования"""
