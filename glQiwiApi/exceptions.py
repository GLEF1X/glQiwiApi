class NoUrlFound(Exception):
    """Данная ошибка возникает при неправильной авторизации yoomoney"""


class RequestProxyError(Exception):
    """Возникает, если были переданы неправильные параметры запроса"""


ProxyError = Exception()


class RequestAuthError(Exception):
    """
    Ошибка при неправильной аунтефикации POST or GET data

    """


class InvalidData(Exception):
    pass


__all__ = ('InvalidData', 'NoUrlFound', 'RequestAuthError', 'RequestProxyError', 'ProxyError')
