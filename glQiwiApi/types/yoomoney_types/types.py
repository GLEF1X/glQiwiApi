from datetime import datetime
from enum import Enum
from typing import Optional, Union, Dict, List, Any

from pydantic import BaseModel, Field, Extra

from glQiwiApi.utils.basics import custom_load


class BalanceDetails(BaseModel):
    """ object: BalanceDetails """
    total: float
    available: float
    deposition_pending: Optional[float] = None
    blocked: Optional[float] = None
    debt: Optional[float] = None
    hold: Optional[float] = None


class CardsLinked(BaseModel):
    """ object: CardsLinked """
    pan_fragment: str
    type: str


class AccountInfo(BaseModel):
    """ object: AccountInfo"""

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

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()


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

    TRANSFERS = 'incoming-transfers-unaccepted'
    """непринятые входящие P2P-переводы любого типа."""


class DigitalGoods(BaseModel):
    """
    Данные о цифровом товаре (пин-коды и бонусы игр, iTunes, Xbox, etc.)
    Поле присутствует при успешном платеже в магазины цифровых товаров.
    Описание формата:
    https://yoomoney.ru/docs/wallet/process-payments/process-payment#digital-goods
    """
    article_id: str = Field(..., alias="merchantArticleId")
    serial: str
    secret: str


class Operation(BaseModel):
    """ object: Operation """

    operation_id: str
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
     у которых был указан параметр label вызова send()
     """

    pattern_id: Optional[str] = None
    """
    Идентификатор шаблона, по которому совершен платеж.
    Присутствует только для платежей.
    """

    details: Optional[Any] = None

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()


class OperationDetails(BaseModel):
    """ object: OperationDetails """
    operation_id: Optional[str] = None
    """Идентификатор операции. Можно получить при вызове метода history()"""

    status: Optional[str] = None
    """Статус платежа (перевода). Можно получить при вызове метода history()"""

    amount: Optional[float] = None
    """Сумма операции (сумма списания со счета)."""

    operation_date: Optional[str] = Field(..., alias="datetime")
    """
    Дата и время совершения операции в формате строки
    в ISO формате с часовым поясом UTC.
    """

    operation_type: Optional[str] = Field(..., alias="type")
    """Тип операции. Возможные значения:
    payment-shop — исходящий платеж в магазин;
    outgoing-transfer — исходящий P2P-перевод любого типа;
    deposition — зачисление;
    incoming-transfer — входящий перевод или перевод до востребования;
    incoming-transfer-protected — входящий перевод с кодом протекции.
    """

    direction: Optional[str] = None
    """
    направление движения средств. может принимать значения:
    - in (приход);
    - out (расход).
    """

    comment: Optional[str] = None
    """
    Комментарий к переводу или пополнению.
    Присутствует в истории отправителя перевода или получателя пополнения.
    """

    digital_goods: Optional[Dict[str, DigitalGoods]] = None
    """
    Данные о цифровом товаре (пин-коды и бонусы игр, iTunes, Xbox, etc.)
    Поле присутствует при успешном платеже в магазины цифровых товаров.
    Описание формата:
    https://yoomoney.ru/docs/wallet/process-payments/process-payment#digital-goods
    """

    details: Optional[str] = None
    """
    Детальное описание платежа. Строка произвольного формата,
    может содержать любые символы и переводы строк
    Необязательный параметр.
    """

    label: Optional[str] = None
    """Метка платежа."""

    answer_datetime: Optional[str] = None
    """
    Дата и время приема или отмены перевода, защищенного кодом протекции.
    Присутствует для входящих и исходящих переводов, защищенных кодом протекции
    если при вызове send вы указали protect=True при передаче аргументов.
    Если перевод еще не принят или не отвергнут получателем, поле отсутствует.
    """

    expires: Optional[str] = None
    """
    Дата и время истечения срока действия кода протекции.
    Присутствует для входящих и исходящих переводов (от/другим) пользователям,
    защищенных кодом протекции,
    если при вызове send вы указали protect=True при передаче аргументов.
    """

    protection_code: Optional[str] = None
    """
    Код протекции.
    Присутствует для исходящих переводов, защищенных кодом протекции.
    """

    codepro: Optional[bool] = None
    """
    Перевод защищен кодом протекции.
    Присутствует для переводов другим пользователям.
    """

    message: Optional[str] = None
    """
    Сообщение получателю перевода.
    Присутствует для переводов другим пользователям.
    """

    recipient_type: Optional[str] = None
    """
    Тип идентификатора получателя перевода. Возможные значения:
    account — номер счета получателя в сервисе ЮMoney;
    phone — номер привязанного мобильного телефона получателя;
    email — электронная почта получателя перевода.
    Присутствует для исходящих переводов другим пользователям.
    """

    recipient: Optional[str] = None
    """
    Идентификатор получателя перевода.
    Присутствует для исходящих переводов другим пользователям.
    """

    sender: Optional[str] = None
    """
    Номер счета отправителя перевода.
    Присутствует для входящих переводов от других пользователей.
    """

    title: Optional[str] = None
    """
    Краткое описание операции (название магазина или источник пополнения).
    """

    fee: Optional[float] = None
    """
    Сумма комиссии.
    Присутствует для исходящих переводов другим пользователям.
    """

    amount_due: Optional[float] = None
    """
    Сумма к получению.
    Присутствует для исходящих переводов другим пользователям.
    """

    pattern_id: Optional[str] = None
    """
    Идентификатор шаблона платежа, по которому совершен платеж.
    Присутствует только для платежей.
    """

    error: Optional[str] = None
    """
    Код ошибки, присутствует при ошибке выполнения запрос
    Возможные ошибки:
    illegal_param_operation_id - неверное значение параметра operation_id
    Все прочие значения - техническая ошибка, повторите вызов метода позднее.
    """

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()


class Wallet(BaseModel):
    """ object: Wallet """
    allowed: bool


class Item(BaseModel):
    """ object: Item """
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
    """ object: Card"""
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


class PreProcessPaymentResponse(BaseModel):
    """
    Объект, который вы получаете при вызове _pre_process_payment.
    При вызове данного метода вы не списываете деньги со своего счёта,
    а условно подготавливаете его к отправке.
    Для отправки денег на счёт используйте метод send()
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
    error: Optional[str] = None
    money_source: Optional[MoneySource] = None
    protection_code: Optional[str] = None
    account_unblock_uri: Optional[str] = None
    ext_action_uri: Optional[str] = None

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()


class Payment(BaseModel):  # lgtm [py/missing-equals #
    """ object: Payment """
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
    Присутствует только при успешном выполнении метода send().
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

    error: Optional[str] = None
    """
    Код ошибки при проведении платежа (пояснение к полю status).
    Присутствует только при ошибках.
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
    если при вызове метода апи send вы указали protect=True
    при передаче аргументов
    """

    def initialize(self, protection_code: str) -> 'Payment':
        self.protection_code = protection_code
        return self

    class Config:
        """ Pydantic config """
        json_loads = custom_load
        extra = Extra.allow

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()


class IncomingTransaction(BaseModel):
    """ object: IncomingTransaction """
    status: str
    protection_code_attempts_available: int
    ext_action_uri: Optional[str] = None
    error: Optional[str] = None

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()


__all__ = (
    'AccountInfo',
    'OperationType',
    'Operation',
    'OperationDetails',
    'PreProcessPaymentResponse',
    'Payment',
    'IncomingTransaction'
)
