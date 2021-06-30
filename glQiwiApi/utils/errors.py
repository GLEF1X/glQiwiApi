import json
from typing import Optional, Union, Dict, Any

from aiohttp import RequestInfo
from pydantic import BaseModel


class NoUrlFound(Exception):
    """Данная ошибка возникает при неправильной авторизации yoomoney"""


class RequestProxyError(Exception):
    """Возникает, если были переданы неправильные параметры запроса"""


class NetworkError(Exception):
    ...


class InvalidCardNumber(Exception):
    """
    Ошибка, при передаче номера карты в неправильном формате

    """


class RequestAuthError(Exception):
    """
    Ошибка при неправильной аутентификации POST or GET data

    """


class InvalidToken(Exception):
    """
    Ошибка, возникающая, если был передан неверный токен

    """


class InvalidData(TypeError):
    """
    Ошибка возникает если были переданы или получены невалидные данные

    """


class NoUpdatesToExecute(Exception):
    """
    Ошибка возбуждается если при полинге нет транзакций, чтобы обрабатывать

    """


class RequestInfoModel(BaseModel):
    method: str
    url: str
    real_url: str


class ExceptionTraceback(BaseModel):
    status_code: int
    msg: Optional[str] = None
    additional_info: Optional[str] = None
    request_info: Optional[RequestInfoModel] = None


class StateError(Exception):
    ...


class InvalidCachePayload(Exception):
    ...


class RequestError(Exception):
    """
    Возникает при ошибках сервиса или неправильной передаче параметров

    """

    def __init__(
        self,
        message: Optional[str],
        status_code: Union[str, int],
        additional_info: Optional[str] = None,
        traceback_info: Optional[Union[RequestInfo, str, bytes, dict]] = None,
    ) -> None:
        super(RequestError, self).__init__()
        self.message = message
        self.status_code = status_code
        self.additional_info = additional_info
        self.traceback_info = traceback_info

    def __str__(self) -> str:
        resp = "code={sc} doc={msg}, additional_info={info}" ""
        return resp.format(
            sc=self.status_code, msg=self.message, info=self.additional_info
        )

    def __repr__(self) -> str:
        return self.__str__()

    def to_model(self) -> ExceptionTraceback:
        """ Convert exception to :class:`ExceptionTraceback` """
        if not isinstance(self.traceback_info, RequestInfo):
            raise TypeError(
                "Cannot convert exception to `ExceptionTraceback`, because "
                "this method require `RequestInfo` object"
            )
        return ExceptionTraceback(
            status_code=self.status_code,
            msg=self.message,
            additional_info=self.additional_info,
            request_info=RequestInfoModel(
                method=self.traceback_info.method,
                url=self.traceback_info.url.__str__(),
                real_url=self.traceback_info.real_url.__str__(),
            ),
        )

    def _make_json_without_request_info(self) -> Dict[str, Any]:
        return {
            "code": self.status_code,
            "msg": self.message,
            "additional_info": self.additional_info,
            "traceback_info": self.traceback_info,
        }

    def json(self, indent: int = 4, **dump_kw) -> str:
        """
        Method, that makes json format from traceback

        :param indent:
        :param dump_kw:
        """
        if isinstance(self.traceback_info, RequestInfo):
            info = self.to_model().dict(exclude_none=True)
        else:
            info = self._make_json_without_request_info()
        return json.dumps(info, indent=indent, ensure_ascii=False, **dump_kw)


__all__ = (
    "InvalidData",
    "NoUrlFound",
    "RequestAuthError",
    "RequestProxyError",
    "InvalidCardNumber",
    "InvalidToken",
    "RequestError",
    "NoUpdatesToExecute",
    "StateError",
    "NetworkError",
    "InvalidCachePayload",
)
