import json
from typing import Optional, Dict, Any, Union


class NoUrlFound(Exception):
    """Данная ошибка возникает при неправильной авторизации yoomoney"""


class RequestProxyError(Exception):
    """Возникает, если были переданы неправильные параметры запроса"""


ProxyError = Exception()


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


class InvalidData(Exception):
    """
    Ошибка возникает, если были переданы или получены невалидные данные

    """


class RequestError(Exception):
    """
    Возникает при ошибках сервиса или неправильной передаче параметров

    """

    def __init__(
            self,
            message: str,
            status_code: str,
            additional_info: Optional[str] = None,
            json_info: Optional[Union[Dict[str, Any], str]] = None
    ) -> None:
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.additional_info = additional_info
        self.json_info = json_info

    def __str__(self) -> str:
        resp = "code={sc} doc={msg}, additional_info={info}"""
        return resp.format(
            sc=self.status_code,
            msg=self.message,
            info=self.additional_info
        )

    def __repr__(self) -> str:
        return self.__str__()

    def json(self) -> str:
        return json.dumps(
            self.__str__() if not self.json_info else self.json_info,
            indent=2,
            ensure_ascii=False
        )


__all__ = (
    'InvalidData',
    'NoUrlFound',
    'RequestAuthError',
    'RequestProxyError',
    'ProxyError',
    'InvalidCardNumber',
    'InvalidToken',
    'RequestError',
)
