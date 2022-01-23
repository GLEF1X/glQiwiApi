import abc
from copy import deepcopy
from typing import Any, Dict


class ApiURLBuilder(abc.ABC):
    base_url: str

    def build_url(self, api_method: str, **kwargs: Any) -> str:
        url = self.base_url + api_method
        try:
            return url.format(**kwargs)
        except KeyError:
            raise TypeError("Bad kwargs for url assembly")
