from glQiwiApi import HttpXParser
from glQiwiApi.exceptions import RequestError
from glQiwiApi.qiwi.basic_qiwi_config import ERROR_CODE_NUMBERS
from glQiwiApi.utils import only_json


class QiwiParser(HttpXParser):
    @only_json
    async def _request(self, *args, **kwargs):
        response = await super(QiwiParser, self)._request(*args, **kwargs)
        if response.status_code != 200:
            self.raise_exception(str(response.status_code))
        return response

    @staticmethod
    def raise_exception(status_code: str) -> None:
        message = ERROR_CODE_NUMBERS.get(str(status_code))
        raise RequestError(message, status_code)
