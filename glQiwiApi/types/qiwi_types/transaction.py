from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field, Extra

from glQiwiApi.types.basics import Sum


class Provider(BaseModel):
    """ object: Provider """
    id: Optional[int] = None
    """ID провайдера в QIWI Wallet"""

    short_name: Optional[str] = Field(default=None, alias="shortName")
    """краткое наименование провайдера"""

    long_name: Optional[str] = Field(alias="longName", const=None)
    """развернутое наименование провайдера"""

    logo_url: Optional[str] = Field(alias="logoUrl", const=None)
    """ссылка на логотип провайдера"""

    description: Optional[str] = None
    """описание провайдера (HTML)"""

    keys: Optional[Union[str, list]] = None
    """список ключевых слов"""

    site_url: Optional[str] = Field(alias="siteUrl", const=None)
    """сайт провайдера"""


class Transaction(BaseModel):
    """ object: Transaction """
    transaction_id: int = Field(alias="txnId")
    """	ID транзакции в сервисе QIWI Кошелек"""

    person_id: int = Field(alias="personId")
    """Номер кошелька"""

    date: datetime
    """
    Для запросов истории платежей - Дата/время платежа,
    во временной зоне запроса (см. параметр startDate).
    Для запросов данных о транзакции - Дата/время платежа, время московское
    """

    error_code: Optional[int] = Field(alias="errorCode", const=None)
    """Код ошибки платежа"""

    error: Optional[str] = None
    """Описание ошибки"""

    status: str
    """
    Статус платежа. Возможные значения:
    WAITING - платеж проводится,
    SUCCESS - успешный платеж,
    ERROR - ошибка платежа.
    """

    type: str
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

    sum: Sum
    """Данные о сумме платежа или пополнения."""

    commission: Sum
    """Данные о комиссии"""

    total: Sum
    """Общие данные о платеже в формате объекта Sum"""

    provider: Provider
    """Данные о провайдере."""

    source: Optional[Provider] = None
    """Служебная информация"""

    comment: Optional[str] = None
    """	Комментарий к платежу"""

    currency_rate: int = Field(alias="currencyRate")
    """Курс конвертации (если применяется в транзакции)"""

    _extras: Optional[dict] = Field(..., alias="extras")
    """Служебная информация"""

    _cheque_ready: bool = Field(..., alias="chequeReady")
    """Специальное поле"""

    _bank_document_available: bool = Field(..., alias="bankDocumentAvailable")
    """Специальное поле"""

    _repeat_payment_enabled: bool = Field(..., alias="repeatPaymentEnabled")
    """Специальное поле"""

    _favorite_payment_enabled: bool = Field(
        ..., alias="favoritePaymentEnabled"
    )
    """Специальное поле"""

    _regular_payment_enabled: bool = Field(..., alias="regularPaymentEnabled")
    """Специальное поле"""

    def __str__(self) -> str:
        return f"""Статус транзакции: {self.status}
Дата проведения платежа: {self.date}
Сумма платежа: {self.sum.amount}
Комментарий: {self.comment if isinstance(self.comment, str) else '-'}
{"Кому" if self.type == "OUT" else "От кого"}: {self.to_account}
"""
