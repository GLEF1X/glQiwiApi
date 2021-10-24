from __future__ import annotations

import abc
from typing import Dict, Any


class SingletonABCMeta(abc.ABCMeta):
    """
    Abstract singleton metaclass, using for routers because in class methods
    it's not possible to get the router object,
    so we need singleton to get the same instances of routers

    """

    _instances: Dict[Any, Any] = {}

    def __call__(cls, *args, **kwargs):  # type: ignore
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonABCMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class AbstractRouter(metaclass=SingletonABCMeta):
    def __init__(self) -> None:
        self.config = self.setup_config()
        self.routes = self.setup_routes()

    @abc.abstractmethod
    def setup_config(self) -> Any:
        raise NotImplementedError

    @abc.abstractmethod
    def setup_routes(self) -> Any:
        raise NotImplementedError

    @staticmethod
    def _format_url_kwargs(url_: str, **kwargs: Any) -> str:
        try:
            return url_.format(**kwargs)
        except KeyError:
            raise TypeError("Bad kwargs for url assembly")

    @abc.abstractmethod
    def build_url(self, api_method: str, **kwargs: Any) -> str:
        """Implementation of building url"""
        raise NotImplementedError
