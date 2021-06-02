import ipaddress
from datetime import datetime
from typing import Optional, List

from pydantic import Field, validator

from glQiwiApi.types.base import Base
from glQiwiApi.types.basics import Sum
from glQiwiApi.types.qiwi_types.currency_parsed import CurrencyModel
from glQiwiApi.utils.currency_util import Currency


class PassInfo(Base):
    """ object: PassInfo """

    last_pass_change: str = Field(alias="lastPassChange")
    next_pass_change: str = Field(alias="nextPassChange")
    password_used: bool = Field(alias="passwordUsed")


class MobilePinInfo(Base):
    """ object: MobilePinInfo """

    last_mobile_pin_change: Optional[
        datetime
    ] = Field(alias="lastMobilePinChange")
    mobile_pin_used: bool = Field(alias="mobilePinUsed")
    next_mobile_pin_change: str = Field(alias="nextMobilePinChange")


class PinInfo(Base):
    """ object: PinInfo """
    pin_used: bool = Field(alias="pinUsed")


class AuthInfo(Base):
    """ object: AuthInfo """
    ip: ipaddress.IPv4Address
    bound_email: Optional[str] = Field(alias="boundEmail", const=None)
    last_login_date: Optional[
        datetime
    ] = Field(alias="lastLoginDate", const=None)
    email_settings: Optional[dict] = Field(alias="emailSettings", const=None)
    mobile_pin_info: MobilePinInfo = Field(alias="mobilePinInfo")
    pass_info: PassInfo = Field(alias="passInfo")
    person_id: int = Field(alias="personId")
    pin_info: PinInfo = Field(alias="pinInfo")
    registration_date: datetime = Field(alias="registrationDate")


class SmsNotification(Base):
    """ object: SmsNotification """
    price: Sum
    enabled: bool
    active: bool
    end_date: Optional[datetime] = Field(alias="endDate", const=None)


class IdentificationInfo(Base):
    """ object: IdentificationInfo """
    bank_alias: str = Field(alias="bankAlias")
    identification_level: str = Field(alias="identificationLevel")
    passport_expired: bool = Field(alias="passportExpired")


class NickName(Base):
    """ object: NickName """
    nickname: Optional[str] = None
    can_change: bool = Field(alias="canChange")
    can_use: bool = Field(alias="canUse")
    description: str = ""


class Feature(Base):
    """ object: Feature """
    feature_id: int = Field(alias="featureId")
    feature_value: str = Field(alias="featureValue")
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")


class ContractInfo(Base):
    """ object: ContractInfo """
    blocked: bool = False
    contract_id: int = Field(alias="contractId")
    creation_date: datetime = Field(alias="creationDate")
    identification_info: List[
        IdentificationInfo
    ] = Field(alias="identificationInfo")
    sms_notification: SmsNotification = Field(alias="smsNotification")
    nickname: NickName
    features: Optional[List[Feature]] = None


class UserInfo(Base):
    """ object: UserInfo """
    default_pay_currency: CurrencyModel = Field(alias="defaultPayCurrency")
    default_pay_source: Optional[
        int
    ] = Field(alias="defaultPaySource", const=None)
    default_pay_account_alias: Optional[
        str
    ] = Field(alias="defaultPayAccountAlias", const=None)
    email: Optional[str] = None
    first_transaction_id: int = Field(alias="firstTxnId")
    language: str
    operator: str
    phone_hash: str = Field(alias="phoneHash")
    promo_enabled: Optional[
        bool
    ] = Field(alias="promoEnabled", const=None)

    @validator("default_pay_currency", pre=True, check_fields=True)
    def humanize_pay_currency(cls, v):
        if not isinstance(v, int):
            return v
        return Currency.get(str(v))


class QiwiAccountInfo(Base):
    """Информация об аккаунте"""
    auth_info: Optional[AuthInfo] = Field(alias="authInfo", const=None)
    contract_info: Optional[
        ContractInfo
    ] = Field(alias="contractInfo", const=None)
    user_info: Optional[UserInfo] = Field(alias="userInfo", const=None)


__all__ = [
    'QiwiAccountInfo'
]
