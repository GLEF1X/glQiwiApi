from dataclasses import dataclass
from enum import Enum
from http.cookies import SimpleCookie
from typing import Literal, Optional, Union, Dict, List
from aiohttp.typedefs import RawHeaders
from aiosocksy import Socks5Auth, Socks4Auth

from glQiwiApi.exceptions import ProxyError


@dataclass(frozen=True)
class Response:
    status_code: int
    response_data: Optional[Union[dict, str, bytes, bytearray, Exception]]
    url: str
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


@dataclass
class Limit:
    currency: str
    rest: Union[float, int]
    max_limit: Union[float, int]
    spent: Union[float, int]
    interval: Dict[str, str]
    limit_type: str
    limit_country_code: Optional[str] = None


@dataclass
class Bill:
    site_id: str
    bill_id: str
    amount: Dict[str, str]
    status: Dict[str, Union[str, Literal['WAITING', 'PAID', 'REJECTED', 'EXPIRED']]]
    creation_date_time: str
    expiration_date_time: str
    pay_url: str
    custom_fields: Optional[Dict[str, str]] = None
    customer: Optional[Dict[str, Union[str, int]]] = None


@dataclass(frozen=True)
class Commission:
    provider_id: int
    withdraw_sum: Dict[str, Union[float, str, int]]
    qw_commission: Dict[str, Union[float, str, int]]
    withdraw_to_enrollment_rate: int = 1


@dataclass
class AccountInfo:
    account: str
    balance: float
    currency: str
    account_type: str
    identified: bool
    account_status: str
    balance_details: Dict[str, float]


class OperationType(Enum):
    """
    Типы операций YooMoney

    deposition — пополнение счета (приход);
    payment — платежи со счета (расход);
    incoming_transfers_unaccepted —
    непринятые входящие P2P-переводы любого типа.

    """
    DEPOSITION = 'deposition'
    PAYMENT = 'payment'
    INCOMING = 'incoming-transfers-unaccepted'


ALL_OPERATION_TYPES = [OperationType.DEPOSITION, OperationType.PAYMENT, OperationType.INCOMING]


@dataclass(frozen=True)
class Operation:
    operation_id: str
    status: str
    operation_date: str
    title: str
    direction: str
    amount: Union[int, float]
    operation_type: str
    label: Optional[str] = None
    pattern_id: Optional[str] = None


@dataclass(frozen=True)
class OperationDetails:
    operation_id: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[float] = None
    operation_date: Optional[str] = None
    operation_type: Optional[str] = None
    direction: Optional[Literal['in', 'out']] = None
    comment: Optional[str] = None
    digital_goods: Optional[Dict[str, Dict[str, List[Dict[str, str]]]]] = None
    details: Optional[str] = None
    label: Optional[str] = None
    answer_datetime: Optional[str] = None
    expires: Optional[str] = None
    protection_code: Optional[str] = None
    codepro: Optional[bool] = None
    message: Optional[str] = None
    recipient_type: Optional[Literal['account', 'phone', 'email']] = None
    recipient: Optional[str] = None
    sender: Optional[str] = None
    title: Optional[str] = None
    fee: Optional[float] = None
    amount_due: Optional[float] = None
    pattern_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class PreProcessPaymentResponse:
    status: Literal['success', 'refused']
    request_id: str
    recipient_account_status: Literal['anonymous', 'named', 'identified']
    fees: Dict[str, float]
    balance: Optional[float] = None
    recipient_account_type: Optional[Literal['personal', 'professional']] = None
    recipient_identified: bool = False
    recipient_masked_account: Optional[str] = None
    multiple_recipients_found: Optional[str] = None
    contract_amount: Optional[float] = None
    error: Optional[str] = None
    money_source: Optional[Dict[str, Dict[str, Union[str, bool, list]]]] = None
    protection_code: Optional[str] = None
    account_unblock_uri: Optional[str] = None
    ext_action_uri: Optional[str] = None


@dataclass
class Payment:
    status: Literal['success', 'refused']
    payment_id: str
    credit_amount: Optional[float] = None
    payer: Optional[str] = None
    payee: Optional[str] = None
    payee_uid: Union[str, int, None] = None
    invoice_id: Optional[str] = None
    balance: Optional[float] = None
    error: Optional[str] = None
    account_unblock_uri: Optional[str] = None
    acs_uri: Optional[str] = None
    acs_params: Optional[str] = None
    next_retry: Optional[int] = None
    digital_goods: Optional[Dict[str, Dict[str, List[Dict[str, str]]]]] = None
    protection_code: Optional[str] = None


__all__ = (
    'Response', 'Bill', 'Commission', 'Limit', 'Identification', 'InvalidCardNumber', 'WrapperData',
    'Transaction', 'ProxyService',
    'proxy_list', 'AccountInfo', 'OperationType', 'ALL_OPERATION_TYPES', 'Operation', 'OperationDetails',
    'PreProcessPaymentResponse', 'Payment'
)
