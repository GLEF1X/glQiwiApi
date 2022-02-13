import ipaddress
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, validator

from glQiwiApi.types.amount import AmountWithCurrency, CurrencyModel
from glQiwiApi.types.base import Base
from glQiwiApi.utils.currency_util import Currency


class PassInfo(Base):
    """object: PassInfo"""

    last_pass_change: str = Field(alias="lastPassChange")
    next_pass_change: str = Field(alias="nextPassChange")
    password_used: bool = Field(alias="passwordUsed")


class MobilePinInfo(Base):
    """object: MobilePinInfo"""

    last_mobile_pin_change: Optional[datetime] = Field(alias="lastMobilePinChange")
    mobile_pin_used: bool = Field(alias="mobilePinUsed")
    next_mobile_pin_change: str = Field(alias="nextMobilePinChange")


class PinInfo(Base):
    """object: PinInfo"""

    pin_used: bool = Field(alias="pinUsed")


class AuthInfo(Base):
    """object: AuthInfo"""

    ip: ipaddress.IPv4Address
    bound_email: Optional[str] = Field(None, alias="boundEmail")
    last_login_date: Optional[datetime] = Field(None, alias="lastLoginDate")
    email_settings: Optional[Dict[Any, Any]] = Field(None, alias="emailSettings")
    mobile_pin_info: MobilePinInfo = Field(alias="mobilePinInfo")
    pass_info: PassInfo = Field(alias="passInfo")
    person_id: int = Field(alias="personId")
    pin_info: PinInfo = Field(alias="pinInfo")
    registration_date: datetime = Field(alias="registrationDate")


class SmsNotification(Base):
    """object: SmsNotification"""

    price: AmountWithCurrency
    enabled: bool
    active: bool
    end_date: Optional[datetime] = Field(None, alias="endDate")


class IdentificationInfo(Base):
    """object: IdentificationInfo"""

    bank_alias: Optional[str] = Field(None, alias="bankAlias")
    identification_level: Optional[str] = Field(None, alias="identificationLevel")
    passport_expired: Optional[bool] = Field(None, alias="passportExpired")


class NickName(Base):
    """object: NickName"""

    nickname: Optional[str] = None
    can_change: bool = Field(alias="canChange")
    can_use: bool = Field(alias="canUse")
    description: str = ""


class Feature(Base):
    """object: Feature"""

    feature_id: int = Field(alias="featureId")
    feature_value: str = Field(alias="featureValue")
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")


class ContractInfo(Base):
    """object: ContractInfo"""

    blocked: bool = False
    contract_id: int = Field(alias="contractId")
    creation_date: datetime = Field(alias="creationDate")
    identification_info: List[IdentificationInfo] = Field(alias="identificationInfo")
    sms_notification: SmsNotification = Field(alias="smsNotification")
    nickname: NickName
    features: Optional[List[Feature]] = None


class UserInfo(Base):
    """object: UserInfo"""

    default_pay_currency: CurrencyModel = Field(..., alias="defaultPayCurrency")
    default_pay_source: Optional[int] = Field(None, alias="defaultPaySource")
    default_pay_account_alias: Optional[str] = Field(None, alias="defaultPayAccountAlias")
    email: Optional[str] = None
    first_transaction_id: Union[str, int, None] = Field(None, alias="firstTxnId")
    language: str
    operator: str
    phone_hash: str = Field(alias="phoneHash")
    promo_enabled: Optional[bool] = Field(None, alias="promoEnabled")

    @validator("default_pay_currency", pre=True)
    def humanize_pay_currency(cls, v):  # type: ignore
        if not isinstance(v, int):
            return v
        return Currency.get(str(v))


class UserProfile(Base):
    auth_info: Optional[AuthInfo] = Field(None, alias="authInfo")
    contract_info: Optional[ContractInfo] = Field(None, alias="contractInfo")
    user_info: Optional[UserInfo] = Field(None, alias="userInfo")


__all__ = ["UserProfile"]
