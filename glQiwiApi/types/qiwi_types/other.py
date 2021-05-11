from pydantic import BaseModel, Field


class CrossRate(BaseModel):
    """Курс валюты"""
    rate_from: str = Field(..., alias="from")
    rate_to: str = Field(..., alias="to")
    rate: float


class PaymentMethod(BaseModel):
    payment_type: str
    account_id: str


class FreePaymentDetailsFields(BaseModel):
    """ Набор реквизитов платежа"""
    name: str
    """Наименование банка получателя"""

    extra_to_bik: str
    """БИК банка получателя"""

    to_bik: str
    """	БИК банка получателя"""

    city: str
    """Город местонахождения получателя"""

    info: str = 'Коммерческие организации'
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

__all__ = ('CrossRate', 'FreePaymentDetailsFields', 'PaymentMethod')
