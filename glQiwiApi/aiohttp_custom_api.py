from typing import Dict, Optional, Any, Union

import glQiwiApi
from glQiwiApi.basic_requests_api import HttpXParser, SimpleCache
from glQiwiApi.types.basics import CachedResponse
from glQiwiApi.utils.exceptions import RequestError, InvalidData


class CustomParser(HttpXParser):
    """
    Немного переделанный дочерний класс HttpXParser
    под платежные системы и кэширование запросов

    """

    def __init__(
            self,
            without_context: bool,
            messages: Dict[str, str],
            cache_time: Union[float, int]
    ) -> None:
        super(CustomParser, self).__init__()
        if isinstance(cache_time, (int, float)):
            if cache_time > 80:
                raise InvalidData(
                    "Время кэширование должно быть не больше 80-ти секунд"
                )
        self._without_context = without_context
        self.messages = messages
        self._cache = SimpleCache(cache_time)

    async def _request(self, *args, **kwargs):
        # Получаем текущий кэш используя ссылку как ключ
        response = self._cache.get_current(kwargs.get('url'))
        if not self._cache.validate(kwargs):
            response = await super()._request(*args, **kwargs)

        if not isinstance(response, CachedResponse):
            if response.status_code != 200:
                self.raise_exception(
                    response.status_code,
                    json_info=response.response_data
                )

            if self._without_context:
                await self.session.close()

        self._cache.set(
            result=response.response_data,
            kwargs=kwargs,
            status_code=response.status_code
        )
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
