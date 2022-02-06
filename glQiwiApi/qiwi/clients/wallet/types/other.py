from typing import Union

from pydantic import Field, validator

from glQiwiApi.types.amount import CurrencyModel
from glQiwiApi.types.base import HashableBase, Base
from glQiwiApi.utils.currency_util import Currency


class CrossRate(HashableBase):
    """Курс валюты"""

    rate_from: Union[str, CurrencyModel] = Field(..., alias="from")
    rate_to: Union[str, CurrencyModel] = Field(..., alias="to")
    rate: float

    @validator("rate_from", "rate_to", pre=True)
    def humanize_rates(cls, v):  # type: ignore
        if not isinstance(v, str):
            return v
        cur = Currency.get(v)
        if not cur:
            return v
        return cur


class PaymentMethod(Base):
    payment_type: str
    account_id: str


class PaymentDetails(Base):
    """Набор реквизитов платежа"""

    name: str
    """Наименование банка получателя"""

    extra_to_bik: str
    """БИК банка получателя"""

    to_bik: str
    """	БИК банка получателя"""

    city: str
    """Город местонахождения получателя"""

    info: str = "Коммерческие организации"
    """Константное значение"""

    is_commercial: str = "1"
    """Служебная информация"""

    to_name: str
    """Наименование организации"""

    to_inn: str
    """ИНН организации"""

    to_kpp: str
    """	КПП организации"""

    nds: str
    """
    Признак уплаты НДС.
    Если вы оплачиваете квитанцию и в ней не указан НДС,
    то строка НДС не облагается. В ином случае, строка В т.ч. НДС
    """

    goal: str
    """Назначение платежа"""

    urgent: str = "0"
    """
    Признак срочного платежа (0 - нет, 1 - да).
    Срочный платеж выполняется от 10 минут.
    Возможен по будням с 9:00 до 20:30 по московскому времени.
    Стоимость услуги — 25 рублей.
    """

    account: str
    """Номер счета получателя"""

    from_name: str
    """Имя плательщика"""

    from_name_p: str
    """Отчество плательщика"""

    from_name_f: str
    """	Фамилия плательщика"""

    requestProtocol: str = "qw1"
    """Служебная информация, константа"""

    toServiceId: str = "1717"
    """Служебная информация, константа"""


__all__ = ("CrossRate", "PaymentDetails", "PaymentMethod")
