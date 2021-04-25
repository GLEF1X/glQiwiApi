from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field

from glQiwiApi.types.basics import Sum
from glQiwiApi.utils.basics import custom_load


class Provider(BaseModel):
    """ object: Provider """
    id: int
    """ID провайдера в QIWI Wallet"""

    short_name: str = Field(alias="shortName")
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

    source: Provider
    """Служебная информация"""

    comment: Optional[str] = None
    """	Комментарий к платежу"""

    currency_rate: int = Field(alias="currencyRate")
    """Курс конвертации (если применяется в транзакции)"""

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()

    def as_str(self):
        return f"""Статус транзакции: {self.status}
Дата проведения платежа: {self.date}
Сумма платежа: {self.sum.amount}
Комментарий: {self.comment if isinstance(self.comment, str) else '-'}
"""
