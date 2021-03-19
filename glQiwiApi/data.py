from dataclasses import dataclass
from http.cookies import SimpleCookie
from typing import Literal, Optional, Union, Dict

from aiohttp.typedefs import RawHeaders
from aiosocksy import Socks5Auth, Socks4Auth

ProxyError = Exception()


@dataclass(frozen=True)
class Response:
    status_code: int
    response_data: Optional[Union[dict, str, bytes, bytearray, Exception]]
    raw_headers: Optional[RawHeaders] = None
    cookies: Optional[SimpleCookie] = None
    ok: bool = False
    content_type: Optional[str] = None
    host: Optional[str] = None

    @classmethod
    def bad_response(cls) -> 'Response':
        return cls(
            status_code=500,
            response_data=ProxyError
        )


@dataclass
class ProxyService:
    login: str
    password: str
    ip_address: str
    service_type: Literal['SOCKS5', 'SOCKS4'] = 'SOCKS5'
    proxy_auth: Optional[Socks5Auth] = None
    socks_url: Optional[str] = None

    def get_proxy(self) -> Dict[str, Union[str, Socks5Auth]]:
        if not isinstance(self.proxy_auth, (Socks5Auth, Socks4Auth)):
            self.proxy_auth = Socks5Auth(
                login=self.login,
                password=self.password
            )

        self.socks_url = '{socks_type}://{ip_address}'.format(
            socks_type=self.service_type.lower(),
            ip_address=self.ip_address
        )
        return dict(
            proxy_auth=self.proxy_auth,
            proxy=self.socks_url
        )


class RequestAuthError(Exception):
    """
    Ошибка при неправильной аунтефикации POST or GET data

    """


proxy_list = (
    ProxyService(
        login='6TA3h0',
        password='3qHCjh',
        ip_address='91.241.47.240:8000'
    ),
)


@dataclass
class WrapperData:
    headers: Dict[str, Union[str, int]]
    data: Dict[str, Union[str, Dict[str, str]]] = None
    json: Dict[str, Union[str, Dict[str, str]]] = None
    cookies: Optional[Dict[str, Union[str, int]]] = None


class InvalidCardNumber(Exception):
    pass


@dataclass(frozen=True)
class Transaction:
    transaction_id: int
    person_id: int
    date: str
    type: Literal['IN', 'OUT', 'QIWI_CARD']
    sum: Dict[str, int]
    commission: Dict[str, int]
    total: Dict[str, int]
    to_account: str
    comment: Optional[str] = None


@dataclass(frozen=True)
class Identification:
    identification_id: int
    first_name: str
    middle_name: str
    last_name: str
    birth_date: str
    passport: str
    inn: str
    snils: str
    oms: str
    type: str
