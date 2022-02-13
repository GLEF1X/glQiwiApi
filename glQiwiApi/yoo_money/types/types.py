from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Iterator, TYPE_CHECKING

from pydantic import BaseModel, Field, root_validator, ValidationError

from glQiwiApi.types.base import Base

if TYPE_CHECKING:
    from glQiwiApi import YooMoneyAPI  # noqa


class JsonErr(BaseModel):
    error_code: str = Field(..., alias="error")


class Response(Base):
    error: Optional[str] = None

    @root_validator(pre=True)
    def _check_error(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        from glQiwiApi.yoo_money.exceptions import match_error

        try:
            err = JsonErr.parse_obj(values)
        except ValidationError:
            return values
        match_error(err.error_code)
        return values


class BalanceDetails(Response):
    """object: BalanceDetails"""

    total: float
    available: float
    deposition_pending: Optional[float] = None
    blocked: Optional[float] = None
    debt: Optional[float] = None
    hold: Optional[float] = None


class CardsLinked(BaseModel):
    """object: CardsLinked"""

    pan_fragment: str
    type: str


class AccountInfo(Response):
    """object: AccountInfo"""

    account: str
    """Номер счета"""

    balance: float
    """Баланс счета"""

    currency: str
    """
    Код валюты счета пользователя.
    Всегда 643 (рубль РФ по стандарту ISO 4217).
    """

    identified: bool
    """Верифицирован ли кошелек"""

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
    Блок появляется, если сейчас или когда-либо ранее были зачисления в очереди
    задолженности, блокировки средств.
    """

    cards_linked: Optional[List[CardsLinked]] = None
    """
    Информация о привязанных банковских картах.
    Если к счету не привязано ни одной карты, параметр отсутствует.
    Если к счету привязана хотя бы одна карта,
    параметр содержит список данных о привязанных картах.
    pan_fragment - string Маскированный номер карты.
    type: string
    Тип карты. Может отсутствовать, если неизвестен. Возможные значения:
    - VISA;
    - MasterCard;
    - AmericanExpress;
    - JCB.
    """


class DigitalGoods(Response):
    """
    Данные о цифровом товаре (пин-коды и бонусы игр, iTunes, Xbox, etc.)
    Поле присутствует при успешном платеже в магазины цифровых товаров.
    Описание формата:
    https://yoomoney.ru/docs/wallet/process-payments/process-payment#digital-goods
    """

    article_id: str = Field(..., alias="merchantArticleId")
    serial: str
    secret: str


class Operation(Response):
    """object: Operation"""

    id: str = Field(..., alias="operation_id")
    """Идентификатор операции."""

    status: str
    """
    Статус платежа (перевода). Может принимать следующие значения:
    - success — платеж завершен успешно;
    - refused — платеж отвергнут получателем или отменен отправителем;
    - in_progress — платеж не завершен,
     перевод не принят получателем или ожидает ввода кода протекции.
    """

    operation_date: datetime = Field(..., alias="datetime")
    """
    Дата и время совершения операции в формате строки
    в ISO формате с часовым поясом UTC.
    """

    title: str
    """
    Краткое описание операции (название магазина или источник пополнения).
    """

    direction: str
    """
    Направление движения средств. Может принимать значения:
    - in (приход);
    - out (расход).
    """

    amount: Union[int, float]
    """Сумма операции."""

    operation_type: str = Field(..., alias="type")
    """Тип операции. Возможные значения:
    payment-shop — исходящий платеж в магазин;
    outgoing-transfer — исходящий P2P-перевод любого типа;
    deposition — зачисление;
    incoming-transfer — входящий перевод или перевод до востребования;
    incoming-transfer-protected — входящий перевод с кодом протекции.
    """

    label: Optional[str] = None
    """Метка платежа.
     Присутствует для входящих и исходящих переводов другим пользователям
     у которых был указан параметр label вызова transfer_money()
     """

    pattern_id: Optional[str] = None
    """
    Идентификатор шаблона, по которому совершен платеж.
    Присутствует только для платежей.
    """

    details: Optional[str] = None


class OperationHistory(Response):
    next_record: Optional[int]
    operations: List[Operation]

    def __iter__(self) -> Iterator[Operation]:  # type: ignore
        for operation in self.operations:
            yield operation


class OperationDetails(Response):
    """object: OperationDetails"""

    @root_validator(pre=True)
    def _extract_amount_and_comment_by_operation_type(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Any]:
        operation_type: str = values["type"]
        if operation_type == "payment":
            values["amount"] = values["amount_due"]
            values["comment"] = values["message"]
        return values

    id: str = Field(..., alias="operation_id")
    status: str
    amount: float
    currency: str = Field(..., alias="amount_currency")
    available_operations: List[str]
    operation_date: datetime = Field(..., alias="datetime")
    operation_type: str = Field(..., alias="type")
    direction: str
    title: str
    details: Optional[str] = None
    digital_goods: Optional[Dict[str, DigitalGoods]] = None
    comment: Optional[str] = None
    label: Optional[str] = None
    answer_datetime: Optional[str] = None
    expires: Optional[datetime] = None
    protection_code: Optional[str] = None
    is_secure: bool = Field(default=False, alias="codepro")
    recipient_type: Optional[str] = None
    recipient: Optional[str] = None
    sender: Optional[str] = None
    fee: Optional[float] = None
    pattern_id: Optional[str] = None


class Wallet(BaseModel):
    """object: Wallet"""

    allowed: bool


class Item(Response):
    """object: Item"""

    item_id: str = Field(..., alias="id")
    """
    Идентификатор привязанной к счету банковской карты.
    Его необходимо указать в методе process-payment для
    совершения платежа выбранной картой.
    """
    pan_fragment: str
    """
    Фрагмент номера банковской карты.
    Поле присутствует только для привязанной банковской карты.
    Может отсутствовать, если неизвестен.
    """
    item_type: str = Field(..., alias="type")
    """
    Тип карты. Может отсутствовать, если неизвестен. Возможные значения:
    Visa;
    MasterCard;
    American Express;
    JCB.
    """


class Card(BaseModel):
    """object: Card"""

    allowed: bool
    csc_required: bool
    items: List[Item]


class MoneySource(BaseModel):
    """
    Список доступных методов для проведения данного платежа.
    Каждый метод содержит набор атрибутов.
    """

    wallet: Wallet
    """платеж со счета пользователя"""
    cards: Optional[Card] = None
    """платеж с банковских карт, привязанных к счету"""


class RequestPaymentResponse(Response):
    """
    Объект, который вы получаете при вызове make_request_payment.
    При вызове данного метода вы не списываете деньги со своего счёта,
    а условно подготавливаете его к отправке.
    Для отправки денег на счёт используйте метод transfer_money()
    """

    status: str
    request_id: str
    recipient_account_status: str
    fees: Dict[str, float]
    balance: Optional[float] = None
    recipient_account_type: Optional[str] = None
    recipient_identified: bool = False
    recipient_masked_account: Optional[str] = None
    multiple_recipients_found: Optional[str] = None
    contract_amount: Optional[float] = None
    money_source: Optional[MoneySource] = None
    protection_code: Optional[str] = None
    account_unblock_uri: Optional[str] = None
    ext_action_uri: Optional[str] = None


class Payment(Response):
    """object: Payment"""

    status: str
    """
    Код результата выполнения операции. Возможные значения:
    success — успешное выполнение (платеж проведен).
    Это конечное состояние платежа.
    refused — отказ в проведении платежа.
    Причина отказа возвращается в поле error. Это конечное состояние платежа.
    in_progress — авторизация платежа не завершена.
    Приложению следует повторить запрос
    с теми же параметрами спустя некоторое время.
    ext_auth_required — для завершения авторизации платежа
    с использованием банковской карты
    требуется аутентификация по технологии 3‑D Secure.
    все прочие значения — состояние платежа неизвестно.
    Приложению следует повторить запрос с теми же параметрами
    спустя некоторое время.
    """

    payment_id: str
    """
    Идентификатор проведенного платежа.
    Присутствует только при успешном выполнении метода transfer_money().
    """

    credit_amount: Optional[float] = None
    """
    Сумма, поступившая на счет получателя.
    Присутствует при успешном переводе средств
    на счет другого пользователя ЮMoney.
    """

    payer: Optional[str] = None
    """
    Номер счета плательщика.
    Присутствует при успешном переводе средств
    на счет другого пользователя ЮMoney.
    """

    payee: Optional[str] = None
    """
    Номер счета получателя.
    Присутствует при успешном переводе средств
    на счет другого пользователя ЮMoney.
    """

    payee_uid: Union[str, int, None] = None
    """Служебное значение, не фигурирует в документации"""

    invoice_id: Optional[str] = None
    """
    Номер транзакции магазина в ЮMoney.
    Присутствует при успешном выполнении платежа в магазин.
    """

    balance: Optional[float] = None
    """
    Баланс счета пользователя после проведения платежа.
    Присутствует только при выполнении следующих условий:
    - метод выполнен успешно;
    - токен авторизации обладает правом account-info.
    """

    account_unblock_uri: Optional[str] = None
    """
    Адрес, на который необходимо отправить пользователя для разблокировки счета
    Поле присутствует в случае ошибки account_blocked.
    """

    acs_uri: Optional[str] = None

    acs_params: Optional[str] = None

    next_retry: Optional[int] = None
    """
    Рекомендуемое время,
    спустя которое следует повторить запрос, в миллисекундах.
    Поле присутствует при status=in_progress.
    """

    digital_goods: Optional[Dict[str, Dict[str, List[DigitalGoods]]]] = None

    protection_code: Optional[str] = None
    """
    Код протекции, который был сгенерирован,
    если при вызове метода апи transfer_money вы указали protect=True
    при передаче аргументов
    """

    def initialize(self, protection_code: Optional[str]) -> "Payment":
        self.protection_code = protection_code
        return self


class IncomingTransaction(Response):
    """object: IncomingTransaction"""

    status: str
    protection_code_attempts_available: int
    ext_action_uri: Optional[str] = None
