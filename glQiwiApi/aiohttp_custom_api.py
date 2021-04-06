from typing import Dict, Optional, Any

import glQiwiApi
from glQiwiApi.api import HttpXParser
from glQiwiApi.utils.exceptions import RequestError


class CustomParser(HttpXParser):

    def __init__(self, without_context: bool, messages: Dict[str, str]) -> None:
        super(CustomParser, self).__init__()
        self._without_context = without_context
        self.messages = messages

    async def _request(self, *args, **kwargs):
        response = await super(CustomParser, self)._request(*args, **kwargs)
        if response.status_code != 200:
            self.raise_exception(str(response.status_code), json_info=response.response_data)
        if self._without_context:
            await self.session.close()

        return response

    def raise_exception(self, status_code: str, json_info: Optional[Dict[str, Any]] = None) -> None:
        message = self.messages.get(str(status_code), "Unknown")
        raise RequestError(message, status_code, additional_info=f"{glQiwiApi.__version__} version api",
                           json_info=json_info)
