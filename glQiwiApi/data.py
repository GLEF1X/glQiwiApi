from dataclasses import dataclass
from enum import Enum
from http.cookies import SimpleCookie
from typing import Literal, Optional, Union, Dict, List, Any

from aiohttp.typedefs import RawHeaders
from aiosocksy import Socks5Auth, Socks4Auth

from glQiwiApi.exceptions import ProxyError


@dataclass(frozen=True)
class Response:
    status_code: int
    response_data: Optional[Union[dict, str, bytes, bytearray, Exception]]
    url: Optional[str] = None
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


@dataclass
class Sum:
    amount: Union[int, float, str]
    currency: str


@dataclass(frozen=True)
class Transaction:
    transaction_id: int
    """	ID транзакции в сервисе QIWI Кошелек"""

    person_id: int
    """Номер кошелька"""

    date: str
    """
    Для запросов истории платежей - Дата/время платежа, во временной зоне запроса (см. параметр startDate).
    Для запросов данных о транзакции - Дата/время платежа, время московское
    """

    type: Literal['IN', 'OUT', 'QIWI_CARD']
    """
    Тип платежа. Возможные значения:
    IN - пополнение,
    OUT - платеж,
    QIWI_CARD - платеж с карт QIWI (QVC, QVP).
    """
    sum: Sum
    """Данные о сумме платежа или пополнения."""

    commission: Sum
    """Данные о комиссии"""

    total: Sum
    """Общие данные о платеже в формате объекта Sum"""

    to_account: str
    """
    Для платежей - номер счета получателя.
    Для пополнений - номер отправителя, терминала или название агента пополнения кошелька
    """
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
class Interval:
    dateFrom: str
    dateTill: str


@dataclass
class Limit:
    currency: str
    rest: Union[float, int]
    max_limit: Union[float, int]
    spent: Union[float, int]
    interval: Interval
    limit_type: str
    limit_country_code: Optional[str] = None


@dataclass
class BillStatus:
    value: Literal['WAITING', 'PAID', 'REJECTED', 'EXPIRED']
    changedDateTime: str


@dataclass
class Customer:
    phone: str
    email: str
    account: str


@dataclass
class Bill:
    site_id: str
    bill_id: str
    amount: Sum
    status: BillStatus
    creation_date_time: str
    expiration_date_time: str
    pay_url: str
    custom_fields: Optional[Dict[str, str]] = None
    customer: Optional[Customer] = None


@dataclass(frozen=True)
class Commission:
    provider_id: int
    withdraw_sum: Sum
    qw_commission: Sum
    withdraw_to_enrollment_rate: int = 1


# YooMoney objects

@dataclass
class BalanceDetails:
    total: float
    available: float
    deposition_pending: Optional[float] = None
    blocked: Optional[float] = None
    debt: Optional[float] = None
    hold: Optional[float] = None


@dataclass
class AccountInfo:
    account: str
    """Номер счета"""

    balance: float
    """Баланс счета"""

    currency: str
    """Код валюты счета пользователя. Всегда 643 (рубль РФ по стандарту ISO 4217)."""

    identified: bool
    """Индентификацирован ли кошелек"""

    account_type: str
    """
    Тип счета пользователя. Возможные значения:
    personal — счет пользователя в ЮMoney;
    professional — профессиональный счет в ЮMoney
    """

    account_status: str
    """
    Статус пользователя. Возможные значения:
    anonymous — анонимный счет;
    named — именной счет;
    identified — идентифицированный счет.
    """

    balance_details: BalanceDetails
    """
    Расширенная информация о балансе. 
    По умолчанию этот блок отсутствует.
    Блок появляется, если сейчас или когда-либо ранее были зачисления в очереди, задолженности, блокировки средств.
    """

    cards_linked: Optional[List[Dict[str, str]]] = None
    """
    Информация о привязанных банковских картах.
    Если к счету не привязано ни одной карты, параметр отсутствует.
    Если к счету привязана хотя бы одна карта, параметр содержит список данных о привязанных картах.
    pan_fragment	string	Маскированный номер карты.
    type	string	
    Тип карты. Может отсутствовать, если неизвестен. Возможные значения:
    - VISA;
    - MasterCard;
    - AmericanExpress;
    - JCB.
    """


class OperationType(Enum):
    """
    Типы операций YooMoney

    deposition — пополнение счета (приход);
    payment — платежи со счета (расход);
    incoming_transfers_unaccepted —
    непринятые входящие P2P-переводы любого типа.

    """
    DEPOSITION = 'deposition'
    """Пополнение счета (приход);"""

    PAYMENT = 'payment'
    """Платежи со счета (расход)"""

    INCOMING = 'incoming-transfers-unaccepted'
    """непринятые входящие P2P-переводы любого типа."""


ALL_OPERATION_TYPES = [OperationType.DEPOSITION, OperationType.PAYMENT, OperationType.INCOMING]


@dataclass(frozen=True)
class Operation:
    operation_id: str
    """Идентификатор операции."""

    status: str
    """
    Статус платежа (перевода). Может принимать следующие значения:
    - success — платеж завершен успешно;
    - refused — платеж отвергнут получателем или отменен отправителем;
    - in_progress — платеж не завершен, перевод не принят получателем или ожидает ввода кода протекции.
    """

    operation_date: str
    """Дата и время совершения операции в формате строки в ISO формате с часовым поясом UTC."""

    title: str
    """Краткое описание операции (название магазина или источник пополнения)."""

    direction: str
    """
    Направление движения средств. Может принимать значения:
    - in (приход);
    - out (расход).
    """

    amount: Union[int, float]
    """Сумма операции."""

    operation_type: str
    """Тип операции. Возможные значения:
    payment-shop — исходящий платеж в магазин;
    outgoing-transfer — исходящий P2P-перевод любого типа;
    deposition — зачисление;
    incoming-transfer — входящий перевод или перевод до востребования;
    incoming-transfer-protected — входящий перевод с кодом протекции.
    """

    label: Optional[str] = None
    """Метка платежа.
     Присутствует для входящих и исходящих переводов другим пользователям ЮMoney,
     у которых был указан параметр label вызова send()
     """

    pattern_id: Optional[str] = None
    """Идентификатор шаблона, по которому совершен платеж. Присутствует только для платежей."""

    details: Optional[Any] = None


@dataclass(frozen=True)
class OperationDetails:
    operation_id: Optional[str] = None
    """Идентификатор операции. Можно получить при вызове метода history()"""

    status: Optional[str] = None
    """Статус платежа (перевода). Можно получить при вызове метода history()"""

    amount: Optional[float] = None
    """Сумма операции (сумма списания со счета)."""

    operation_date: Optional[str] = None
    """Дата и время совершения операции в формате строки в ISO формате с часовым поясом UTC."""

    operation_type: Optional[str] = None
    """Тип операции. Возможные значения:
    payment-shop — исходящий платеж в магазин;
    outgoing-transfer — исходящий P2P-перевод любого типа;
    deposition — зачисление;
    incoming-transfer — входящий перевод или перевод до востребования;
    incoming-transfer-protected — входящий перевод с кодом протекции.
    """

    direction: Optional[Literal['in', 'out']] = None
    """
    Направление движения средств. Может принимать значения:
    - in (приход);
    - out (расход).
    """

    comment: Optional[str] = None
    """Комментарий к переводу или пополнению. Присутствует в истории отправителя перевода или получателя пополнения."""

    digital_goods: Optional[Dict[str, Dict[str, List[Dict[str, str]]]]] = None
    """
    Данные о цифровом товаре (пин-коды и бонусы игр, iTunes, Xbox, etc.)
    Поле присутствует при успешном платеже в магазины цифровых товаров.
    Описание формата: https://yoomoney.ru/docs/wallet/process-payments/process-payment#digital-goods
    """

    details: Optional[str] = None
    """
    Детальное описание платежа.
    Строка произвольного формата, может содержать любые символы и переводы строк.
    Необязательный параметр.
    """

    label: Optional[str] = None
    """Метка платежа."""

    answer_datetime: Optional[str] = None
    """
    Дата и время приема или отмены перевода, защищенного кодом протекции.
    Присутствует для входящих и исходящих переводов, защищенных кодом протекции,
     если при вызове метода апи send вы указали protect=True в агрументах.
    Если перевод еще не принят или не отвергнут получателем, поле отсутствует.
    """

    expires: Optional[str] = None
    """
    Дата и время истечения срока действия кода протекции.
    Присутствует для входящих и исходящих переводов (от/другим) пользователям, защищенных кодом протекции,
    если при вызове метода апи send вы указали protect=True в агрументах.
    """

    protection_code: Optional[str] = None
    """Код протекции. Присутствует для исходящих переводов, защищенных кодом протекции."""

    codepro: Optional[bool] = None
    """Перевод защищен кодом протекции. Присутствует для переводов другим пользователям."""

    message: Optional[str] = None
    """Сообщение получателю перевода. Присутствует для переводов другим пользователям."""

    recipient_type: Optional[Literal['account', 'phone', 'email']] = None
    """
    Тип идентификатора получателя перевода. Возможные значения:
    account — номер счета получателя в сервисе ЮMoney;
    phone — номер привязанного мобильного телефона получателя;
    email — электронная почта получателя перевода.
    Присутствует для исходящих переводов другим пользователям.
    """

    recipient: Optional[str] = None
    """Идентификатор получателя перевода. Присутствует для исходящих переводов другим пользователям."""

    sender: Optional[str] = None
    """Номер счета отправителя перевода. Присутствует для входящих переводов от других пользователей."""

    title: Optional[str] = None
    """Краткое описание операции (название магазина или источник пополнения)."""

    fee: Optional[float] = None
    """Сумма комиссии. Присутствует для исходящих переводов другим пользователям."""

    amount_due: Optional[float] = None
    """Сумма к получению. Присутствует для исходящих переводов другим пользователям."""

    pattern_id: Optional[str] = None
    """Идентификатор шаблона платежа, по которому совершен платеж. Присутствует только для платежей."""

    error: Optional[str] = None
    """
    Код ошибки, присутствует при ошибке выполнения запрос
    Возможные ошибки:
    illegal_param_operation_id - неверное значение параметра operation_id
    Все прочие значения - техническая ошибка, повторите вызов метода позднее.
    """


@dataclass
class PreProcessPaymentResponse:
    """
    Объект, который вы получаете при вызове _pre_process_payment.
    При вызове данного метода вы не списываете деньги со своего счёта, а условно подготавливаете его к отправке.
    Для отправки денег на счёт используйте метод send()
    """
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
    status: Literal['success', 'refused', 'in_progress', 'ext_auth_required']
    """
    Код результата выполнения операции. Возможные значения:
    success — успешное выполнение (платеж проведен). Это конечное состояние платежа.
    refused — отказ в проведении платежа. Причина отказа возвращается в поле error. Это конечное состояние платежа.
    in_progress — авторизация платежа не завершена.
     Приложению следует повторить запрос с теми же параметрами спустя некоторое время.
    ext_auth_required — для завершения авторизации платежа с использованием банковской карты
     требуется аутентификация по технологии 3‑D Secure.
    все прочие значения — состояние платежа неизвестно. Приложению следует
     повторить запрос с теми же параметрами спустя некоторое время.
    """

    payment_id: str
    """Идентификатор проведенного платежа. Присутствует только при успешном выполнении метода send()."""

    credit_amount: Optional[float] = None
    """
    Сумма, поступившая на счет получателя.
    Присутствует при успешном переводе средств на счет другого пользователя ЮMoney.
    """

    payer: Optional[str] = None
    """
    Номер счета плательщика. Присутствует при успешном переводе средств на счет другого пользователя ЮMoney.
    """

    payee: Optional[str] = None
    """
    Номер счета получателя. Присутствует при успешном переводе средств на счет другого пользователя ЮMoney.
    """

    payee_uid: Union[str, int, None] = None
    """Служебное значение, не фигурирует в документации"""

    invoice_id: Optional[str] = None
    """Номер транзакции магазина в ЮMoney. Присутствует при успешном выполнении платежа в магазин."""

    balance: Optional[float] = None
    """
    Баланс счета пользователя после проведения платежа. Присутствует только при выполнении следующих условий:
    - метод выполнен успешно;
    - токен авторизации обладает правом account-info.
    """

    error: Optional[str] = None
    """
    Код ошибки при проведении платежа (пояснение к полю status). Присутствует только при ошибках.
    """
    account_unblock_uri: Optional[str] = None
    """
    Адрес, на который необходимо отправить пользователя для разблокировки счета.
    Поле присутствует в случае ошибки account_blocked.
    """

    acs_uri: Optional[str] = None

    acs_params: Optional[str] = None

    next_retry: Optional[int] = None
    """
    Рекомендуемое время, спустя которое следует повторить запрос, в миллисекундах.
     Поле присутствует при status=in_progress.
    """

    digital_goods: Optional[Dict[str, Dict[str, List[Dict[str, str]]]]] = None

    protection_code: Optional[str] = None
    """
    Код протекции, который был сгенерирован, если при вызове метода апи send вы указали protect=True в агрументах
    """


@dataclass(frozen=True)
class IncomingTransaction:
    status: Literal['success', 'refused']
    protection_code_attempts_available: int
    ext_action_uri: Optional[str] = None
    error: Optional[str] = None


__all__ = (
    'Response', 'Bill', 'Commission', 'Limit', 'Identification', 'WrapperData',
    'Transaction', 'ProxyService',
    'proxy_list', 'AccountInfo', 'OperationType', 'ALL_OPERATION_TYPES', 'Operation', 'OperationDetails',
    'PreProcessPaymentResponse', 'Payment', 'IncomingTransaction'
)
