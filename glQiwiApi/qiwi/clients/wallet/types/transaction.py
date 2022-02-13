from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Iterator

from pydantic import Field

from glQiwiApi.types.amount import AmountWithCurrency
from glQiwiApi.types.base import Base


class TransactionType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    ALL = "ALL"
    QIWI_CARD = "QIWI_CARD"


class TransactionStatus(str, enum.Enum):
    WAITING = "WAITING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class Source(str, enum.Enum):
    RUB = "QW_RUB"
    USD = "QW_USD"
    EUR = "QW_EUR"
    CARD = "CARD"
    MK = "MK"


class Provider(Base):
    """object: Provider"""

    id: Optional[int] = None
    """ID провайдера в QIWI Wallet"""

    short_name: Optional[str] = Field(default=None, alias="shortName")
    """краткое наименование провайдера"""

    long_name: Optional[str] = Field(alias="longName", default=None)
    """развернутое наименование провайдера"""

    logo_url: Optional[str] = Field(alias="logoUrl", default=None)
    """ссылка на логотип провайдера"""

    description: Optional[str] = None
    """описание провайдера (HTML)"""

    keys: Optional[Union[str, List[Any]]] = None
    """список ключевых слов"""

    site_url: Optional[str] = Field(alias="siteUrl", default=None)
    """сайт провайдера"""


class Transaction(Base):
    """object: Transaction"""

    id: int = Field(alias="txnId")
    """	ID транзакции в сервисе QIWI Кошелек"""

    person_id: int = Field(alias="personId")
    """Номер кошелька"""

    date: datetime
    """
    Для запросов истории платежей - Дата/время платежа,
    во временной зоне запроса (см. параметр startDate).
    Для запросов данных о транзакции - Дата/время платежа, время московское
    """

    status: TransactionStatus
    """
    Статус платежа. Возможные значения:
    WAITING - платеж проводится,
    SUCCESS - успешный платеж,
    ERROR - ошибка платежа.
    """

    type: TransactionType
    """
    Тип платежа. Возможные значения:
    IN - пополнение,
    OUT - платеж,
    QIWI_CARD - платеж с карт QIWI (QVC, QVP).
    """

    status_text: str = Field(alias="statusText")
    """Текстовое описание статуса платежа"""

    trm_transaction_id: str = Field(alias="trmTxnId")
    """Клиентский ID транзакции"""

    to_account: str = Field(alias="account")
    """
    Для платежей - номер счета получателя.
    Для пополнений - номер отправителя,
    терминала или название агента пополнения кошелька
    """
    sum: AmountWithCurrency
    """Данные о сумме платежа или пополнения."""

    commission: AmountWithCurrency
    """Данные о комиссии"""

    total: AmountWithCurrency
    """Общие данные о платеже в формате объекта Sum"""

    provider: Provider
    """Данные о провайдере."""

    source: Optional[Provider] = None
    """Служебная информация"""

    comment: Optional[str] = None
    """	Комментарий к платежу"""

    currency_rate: int = Field(alias="currencyRate")
    """Курс конвертации (если применяется в транзакции)"""

    _extras: Optional[Dict[Any, Any]] = Field(None, alias="extras")
    """Служебная информация"""

    _cheque_ready: bool = Field(..., alias="chequeReady")
    """Специальное поле"""

    _bank_document_available: bool = Field(..., alias="bankDocumentAvailable")
    """Специальное поле"""

    _repeat_payment_enabled: bool = Field(..., alias="repeatPaymentEnabled")
    """Специальное поле"""

    _favorite_payment_enabled: bool = Field(..., alias="favoritePaymentEnabled")
    """Специальное поле"""

    _regular_payment_enabled: bool = Field(..., alias="regularPaymentEnabled")
    """Специальное поле"""

    class Config:
        use_enum_values = True


class History(Base):
    transactions: List[Transaction] = Field(..., alias="data")
    next_transaction_date: Optional[datetime] = Field(None, alias="nextTxnDate")
    next_transaction_id: Optional[int] = Field(None, alias="nextTxnId")

    def __iter__(self) -> Iterator[Transaction]:  # type: ignore
        for t in self.transactions:
            yield t

    def __len__(self) -> int:
        return len(self.transactions)

    def __str__(self) -> str:
        start_txn_date: Optional[datetime] = None
        end_txn_date: Optional[datetime] = None
        if self.transactions:
            start_txn_date = self.transactions[0].date
            end_txn_date = self.transactions[-1].date
        return (
            f"History from {start_txn_date} to {end_txn_date} | "
            f"next transaction id = {self.next_transaction_id} | size = {len(self)}"
        )

    def sorted_by_id(self) -> History:
        return self.copy(
            exclude={"transactions"},
            update=dict(
                transactions=sorted(self.transactions, key=lambda txn: txn.id)  # type: ignore
            ),
        )

    def sorted_by_date(self, *, from_later_to_earliest: bool = False) -> History:
        return self.copy(
            exclude={"transactions"},
            update=dict(
                transactions=sorted(
                    self.transactions,
                    key=lambda txn: txn.date,  # type: ignore
                    reverse=from_later_to_earliest,
                )
            ),
        )

    def __getitem__(self, i: Any) -> Transaction:
        return self.transactions.__getitem__(i)

    def __bool__(self) -> bool:
        return bool(self.transactions)

    def first(self) -> Transaction:
        return self.transactions[0]

    def last(self) -> Transaction:
        return self.transactions[-1]
