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


class InvalidData(Exception):
    """Ошибка возникает, если были переданы или получены невалид данные при запросе"""


__all__ = ('InvalidData', 'NoUrlFound', 'RequestAuthError', 'RequestProxyError', 'ProxyError', 'InvalidCardNumber')
