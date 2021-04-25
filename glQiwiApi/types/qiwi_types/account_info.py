from datetime import datetime
from typing import Optional, List

from pydantic import Field, BaseModel

from glQiwiApi.types.basics import Sum
from glQiwiApi.utils.basics import custom_load


class PassInfo(BaseModel):
    """ object: PassInfo """

    last_pass_change: str = Field(alias="lastPassChange")
    next_pass_change: str = Field(alias="nextPassChange")
    password_used: bool = Field(alias="passwordUsed")


class MobilePinInfo(BaseModel):
    """ object: MobilePinInfo """

    last_mobile_pin_change: Optional[
        datetime
    ] = Field(alias="lastMobilePinChange")
    mobile_pin_used: bool = Field(alias="mobilePinUsed")
    next_mobile_pin_change: str = Field(alias="nextMobilePinChange")


class PinInfo(BaseModel):
    """ object: PinInfo """
    pin_used: bool = Field(alias="pinUsed")


class AuthInfo(BaseModel):
    """ object: AuthInfo """
    ip: str
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


class SmsNotification(BaseModel):
    """ object: SmsNotification """
    price: Sum
    enabled: bool
    active: bool
    end_date: Optional[datetime] = Field(alias="endDate", const=None)


class IdentificationInfo(BaseModel):
    """ object: IdentificationInfo """
    bank_alias: str = Field(alias="bankAlias")
    identification_level: str = Field(alias="identificationLevel")
    passport_expired: bool = Field(alias="passportExpired")


class NickName(BaseModel):
    """ object: NickName """
    nickname: Optional[str] = None
    can_change: bool = Field(alias="canChange")
    can_use: bool = Field(alias="canUse")
    description: str = ""


class Feature(BaseModel):
    """ object: Feature """
    feature_id: int = Field(alias="featureId")
    feature_value: str = Field(alias="featureValue")
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")


class ContractInfo(BaseModel):
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
    blocked: bool


class UserInfo(BaseModel):
    """ object: UserInfo """
    default_pay_currency: str = Field(alias="defaultPayCurrency")
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


class QiwiAccountInfo(BaseModel):
    """Информация об аккаунте"""
    auth_info: Optional[AuthInfo] = Field(alias="authInfo", const=None)
    contract_info: Optional[
        ContractInfo
    ] = Field(alias="contractInfo", const=None)
    user_info: Optional[UserInfo] = Field(alias="userInfo", const=None)

    class Config:
        """ Pydantic config """
        json_loads = custom_load

        def __str__(self) -> str:
            return f'Config class with loads={self.json_loads}'

        def __repr__(self) -> str:
            return self.__str__()


__all__ = [
    'QiwiAccountInfo'
]
