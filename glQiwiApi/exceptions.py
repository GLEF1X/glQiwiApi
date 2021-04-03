class NoUrlFound(Exception):
    """Данная ошибка возникает при неправильной авторизации yoomoney"""


class RequestProxyError(Exception):
    """Возникает, если были переданы неправильные параметры запроса"""


ProxyError = Exception()


class InvalidCardNumber(Exception):
    """Ошибка, при передаче номера карты в неправильном формате"""


class RequestAuthError(Exception):
    """
    Ошибка при неправильной аунтефикации POST or GET data

    """


class InvalidToken(Exception):
    """Ошибка, возникающая, если был передан неверный токен"""


class InvalidData(Exception):
    """Ошибка возникает, если были переданы или получены невалид данные при запросе"""


class RequestError(Exception):
    """Возникает при ошибках сервиса или неправильной передаче параметров"""

    def __init__(self, message: str, status_code: str, *args):
        super().__init__(*args)
        self.message = message
        self.status_code = status_code

    def __str__(self) -> str:
        return f"code={self.status_code} traceback={self.message}"

    def __repr__(self) -> str:
        return self.__str__()


__all__ = [
    'InvalidData', 'NoUrlFound', 'RequestAuthError', 'RequestProxyError',
    'ProxyError', 'InvalidCardNumber', 'InvalidToken', 'RequestError'
]
