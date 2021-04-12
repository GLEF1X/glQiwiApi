from typing import Dict, Optional, Any, Union

import glQiwiApi
from glQiwiApi.basic_requests_api import HttpXParser
from glQiwiApi.mixins import SimpleCache
from glQiwiApi.types.basics import Attributes
from glQiwiApi.utils.exceptions import RequestError


class CustomParser(HttpXParser):

    def __init__(
            self,
            without_context: bool,
            messages: Dict[str, str]
    ) -> None:
        super(CustomParser, self).__init__()
        self._without_context = without_context
        self.messages = messages
        self._cache = SimpleCache()

    async def _request(self, *args, **kwargs):
        response = self._cache.get()
        if not self._cache.validate(kwargs):
            response = await super(CustomParser, self)._request(*args, **kwargs)

        if response.status_code != 200:
            self.raise_exception(
                response.status_code,
                json_info=response.response_data
            )
        if self._without_context:
            await self.session.close()
        self._cache.set(response, kwargs)
        return response

    def raise_exception(
            self,
            status_code: Union[str, int],
            json_info: Optional[Dict[str, Any]] = None
    ) -> None:
        message = self.messages.get(str(status_code), "Unknown")
        raise RequestError(
            message,
            status_code,
            additional_info=f"{glQiwiApi.__version__} version api",
            json_info=json_info
        )
